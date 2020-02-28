from datetime import date, datetime, timedelta
import random
import string
import time

from django.core.mail import send_mail
from config import celery_app

from explorer import app_settings
from explorer.exporters import get_exporter_class
from explorer.models import Query, QueryLog

from celery.utils.log import get_task_logger
from explorer.utils import (
    s3_upload,
    moni_s3_upload,
    moni_s3_transfer_file_to_ftp,
)

logger = get_task_logger(__name__)


@celery_app.task(name="bulk.execute_query")
def execute_query(query_id, email_address):
    q = Query.objects.get(pk=query_id)
    exporter = get_exporter_class('csv')(q)
    random_part = ''.join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(20)
    )
    url = s3_upload('%s.csv' % random_part, exporter.get_file_output())

    subj = '[SQL Explorer] Report "%s" is ready' % q.title
    msg = 'Download results:\n\r%s' % url

    send_mail(subj, msg, app_settings.FROM_EMAIL, [email_address])


@celery_app.task(name="bulk.snapshot_query")
def snapshot_query(query_id):
    try:
        logger.info("Starting snapshot for query %s..." % query_id)
        q = Query.objects.get(pk=query_id)
        exporter = get_exporter_class('csv')(q)
        k = 'query-%s.snap-%s.csv' % (
            q.id, date.today().strftime('%Y%m%d-%H:%M:%S'))
        logger.info("Uploading snapshot for query %s as %s..." % (query_id, k))
        url = s3_upload(k, exporter.get_file_output())
        logger.info(
            "Done uploading snapshot for query %s. URL: %s" % (query_id, url))
    except Exception:
        logger.exception(
            "Failed to snapshot query %s. Retrying..." % (query_id))
        snapshot_query.retry()


@celery_app.task(name="bulk.snapshot_queries")
def snapshot_queries():
    logger.info("Starting query snapshots...")
    qs = Query.objects.filter(snapshot=True).values_list('id', flat=True)
    for qid in qs:
        snapshot_query.delay(qid)
    logger.info("Done creating tasks.")


@celery_app.task(name="bulk.truncate_querylogs")
def truncate_querylogs(days):
    qs = QueryLog.objects.filter(
        run_at__lt=datetime.now() - timedelta(days=days))
    logger.info(
        'Deleting %s QueryLog objects older than %s days.' % (qs.count, days))
    qs.delete()


@celery_app.task(name="bulk.snapshot_query_on_bucket")
def snapshot_query_on_bucket(query_id=None, *args, **kwrgs):
    try:
        q = Query.objects.get(pk=query_id)
        q_name = q.slug if q.slug else q.id
        exporter = get_exporter_class('csv')(q)
        k = '{}-{}.csv'.format(q_name, date.today().strftime('%Y%m%d'))
        file_output = exporter.get_file_output(encoding=q.encoding)
        # sends the file of the query via all the FTP exports
        for ftp_export in q.ftpexport_set.all():
            moni_s3_transfer_file_to_ftp(
                ftp_export,
                file_output,
                k,
                ftp_export.passive,
            )
            time.sleep(2)
        if q.bucket != '':
            moni_s3_upload(k, file_output, q.bucket)
    except Exception:
        logger.exception("Failed to snapshot query {}.".format(query_id))
    return datetime.now()
