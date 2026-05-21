from events.dispatcher import dispatcher


def run_worker_once(handler):
    """Consume one queued Redis event and hand it to a caller-provided handler.

    The existing app still starts workflows in-process for compatibility. This
    worker function is the migration point for Celery/RQ/Redis workers when the
    deployment grows beyond one API instance.
    """

    event = dispatcher.pop()
    if not event:
        return None
    return handler(event)

