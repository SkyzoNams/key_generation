import http.client
from  scheduled_action.src.Secrets import Encrypt
import logging
logging.basicConfig(format="%(asctime)s: %(levelname)s - %(message)s", level=logging.INFO)
logging.addLevelName(31, "API")
from scheduled_action.src.Config import Config
import time

class API_Caller(object):
    def __init__(self):
        self.connection =  Config().return_config_keys_mover(keys_mover_host=True) + ':' + Config().return_config_keys_mover(keys_mover_port=True)
        self.conn = http.client.HTTPConnection(self.connection)

    """
     @Notice: This function will return the api header with a jwt token
     @Dev:    We use the get_jwt method from the Encrypt file
    """
    def get_header(self):
        return {'authorization': Encrypt().get_jwt()}

    """
     @Notice: This function will send a requestion to the endpoint passed in parameter and the args
     @Dev:    We first build the endpoint using the api_endpoint parameter and the encrypted args then,
              we execute the GET method using requests 
    """
    def send_req(self, api_endpoint: str, args_list: list):
        time.sleep(0.01)
        args_string = "/api/private/%s/" % api_endpoint + "/". \
            join(str(Encrypt().encrypt_message(str(arg)))
                 for arg in args_list) + "/"
        self.conn.request("GET", args_string, headers=self.get_header())
        res = self.conn.getresponse()
        logging.log(31, res)
        data = res.read()
        logging.log(31, data.decode("utf-8"))
        return data.decode("utf-8")


#API_Caller().send_req(api_endpoint="generate_keys", args_list=['1', '2'])
