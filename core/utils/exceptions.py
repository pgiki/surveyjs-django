from rest_framework.views import exception_handler
try:
	from activity_log.middleware import ActivityLog
except Exception as e:
	ActivityLog=None
	# pass

def handler(exc, context):
    # Call REST framework's default exception handler first,
    print("request.data ", context["request"].data)
    print("\n\n\nExceptions",  exc)
    # to get the standard error response.
    if ActivityLog:
        ActivityLog.addLog(context["request"], extraData={"error":f"{exc}"})
    response = exception_handler(exc, context)
    if response is not None:
        response.data['status_code'] = response.status_code
    return response