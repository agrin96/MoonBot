import requests
from typing import Optional,Dict
from datetime import datetime,timezone

import time
import hashlib
import hmac
import base64
import logging

from dotenv import load_dotenv
load_dotenv("../.env")

import os
API_KEY = os.getenv("API_KEY")
SEC_KEY = os.getenv("SEC_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("REQUEST_SYSTEM")

def send_request(
        method:str,
        request_url:str,
        request_params:Optional[str]=None,
        is_public:bool=True,
        recv_window:int=5000)->Dict:
    """Abastraction which handles building and signing API requests.

    Parameters:
        method (str): The HTTP method to use for this call.
        request_url (str): The final url of the request endpoint.
        request_params (Optional[str]): A combined string of request parameters.
        is_public (bool): Whether the request needs a secret signature
        recv_window (int): The time the server has to process your request.
    """
    if request_params is None:
        request_params = ""
    request_params = request_params.replace("\n","")\
        .replace("\t","")\
            .replace(" ","")\
                .strip()

    final_params = request_params
    if not is_public:
        ms_time = int(datetime.now(tz=timezone.utc).timestamp()*1000)
        final_params += F"&timestamp={ms_time}&recvWindow={recv_window}"
        
        signature = hmac.new(
            key=SEC_KEY.encode('utf-8'),
            msg=final_params.encode('utf-8'),
            digestmod=hashlib.sha256).hexdigest()
            
        final_params = F"{final_params}&signature={signature}"
        
    request = requests.Request(
        method=method,
        url=F"{request_url}",
        params=F"{final_params}",
        headers={"X-MBX-APIKEY":API_KEY})
    prepped = request.prepare()

    with requests.Session() as session:
        try:
            r = session.send(prepped)        
            if r:
                if r.status_code == 429:
                    logger.error("Exceeded API limits.")
                    return {
                        "error":429,
                        "retry":r.headers["Retry-After"]}
                if r.status_code == 403:
                    logger.error("Web application firewall violated.")
                    return {
                        "error":403,
                        "retry": 0}
                if r.status_code == 418:
                    logger.error("IP Banned for exceeding API limits.")
                    return {
                        "error":418,
                        "retry":r.headers["Retry-After"]}
                return {
                    "error": 0,
                    "weight": r.headers["X-MBX-USED-WEIGHT"],
                    "data": r.json()}
            logger.error(F"Response error. {r.json()}")
            return {
                "error": 1,
                "msg": F"{r.json()}"
            }
        except Exception as e:
            logger.error(F"Fatal Request error: {e}")
            return None