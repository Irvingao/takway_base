# board cmd
cd /root/examples && nohup python3 touch_request_speak.py > /root/logs/touch_request_speak.log 2>&1 &
cd /root/examples && nohup python3 touch_request_speak.py > /root/logs/touch_request_speak_$(date +"%Y%m%d%H%M%S").log 2>&1 &