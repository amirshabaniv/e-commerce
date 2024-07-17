# from kavenegar import *
from celery import shared_task

@shared_task
def send_otp_code(phone_number, otp):
	pass
	# try:
	# 	api = KavenegarAPI('place your kavenegar api key here')
	# 	params = {
	# 		'sender': '',
	# 		'receptor': phone_number,
	# 		'message': f'{otp} کد تایید شما '
	# 	}
	# 	response = api.sms_send(params)
	# 	print(response)
	# except APIException as e:
	# 	print(e)
	# except HTTPException as e:
	# 	print(e)