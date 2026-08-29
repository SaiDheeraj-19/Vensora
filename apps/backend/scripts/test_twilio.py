import urllib.request
import urllib.parse
import json

def test():
    url = "http://localhost:8000/api/v1/telephony/twilio/incoming"
    data = urllib.parse.urlencode({"CallSid": "CA123", "From": "+1234567890"}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Host", "alabaster-janitor-gauntlet.ngrok-free.dev")
    
    try:
        response = urllib.request.urlopen(req)
        print("Status:", response.status)
        print("XML Response:")
        print(response.read().decode("utf-8"))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test()
