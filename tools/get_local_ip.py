import socket
import requests

# 获取私有IP地址
def get_private_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        private_ip = s.getsockname()[0]
        s.close()
        return private_ip
    except Exception as e:
        print(f"Error getting private IP: {e}")
        return None

# 获取公有IP地址
def get_public_ip():
    try:
        response = requests.get("https://api.ipify.org")
        public_ip = response.text
        return public_ip
    except Exception as e:
        print(f"Error getting public IP: {e}")
        return None

if __name__ == "__main__":
    private_ip = get_private_ip()
    public_ip = get_public_ip()

    print(f"Private IP: {private_ip}")
    print(f"Public IP: {public_ip}")