import asyncio
import logging
from datetime import datetime

try:
    import websockets
except ModuleNotFoundError:
    print("This example relies on the 'websockets' package.")
    print("Please install it by running: ")
    print()
    print(" $ pip install websockets")
    import sys
    sys.exit(1)

from ocpp.routing import on
from ocpp.v16 import ChargePoint as cp
from ocpp.v16.enums import Action, RegistrationStatus, ChargePointErrorCode, ChargePointStatus, AuthorizationStatus
from ocpp.v16 import call_result

logging.basicConfig(level=logging.INFO)


class ChargePoint(cp):
    def __init__(self, id, connection, response_timeout=30):
        super().__init__(id, connection, response_timeout)

    @on(Action.BootNotification)
    def on_boot_notification(self, charge_point_vendor: str, charge_point_model: str, **kwargs):
        return call_result.BootNotificationPayload(
            current_time=datetime.utcnow().isoformat(),
            interval=10,
            status=RegistrationStatus.accepted
        )
    
    @on(Action.Heartbeat)
    def on_heartbeat(self):
        return call_result.HeartbeatPayload(
            current_time=datetime.utcnow().isoformat()
        )

    @on(Action.StatusNotification)
    def on_status_notification(self, connector_id: int, error_code: ChargePointErrorCode, status: ChargePointStatus, **kwargs):
        return call_result.StatusNotificationPayload(
            
        )
    
    @on(Action.Authorize)
    def on_authorize(self, id_tag: str):
        return call_result.AuthorizePayload(
            id_tag_info={ "status" : AuthorizationStatus.accepted, }
        )
    
    @on(Action.StartTransaction)
    def on_start_transaction(self, connector_id: int, id_tag: str, meter_start: int, timestamp: str, **kwargs):
        test = 555
        return call_result.StartTransactionPayload(
            transaction_id=test, 
            id_tag_info={ "status" : AuthorizationStatus.accepted, },
        )

    @on(Action.StopTransaction)
    def on_stop_transaction(self, meter_stop: int, timestamp: str, transaction_id: int, **kwargs):
        return call_result.StopTransactionPayload(
            id_tag_info={ "status" : AuthorizationStatus.accepted, }
        )
    
    @on(Action.MeterValues)
    def on_meter_values(self, connector_id: int, meter_value=[], **kwargs ):
        return call_result.MeterValuesPayload(

        )


async def on_connect(websocket, path):
    """ For every new charge point that connects, create a ChargePoint
    instance and start listening for messages.
    """
    try:
        requested_protocols = websocket.request_headers[
            'Sec-WebSocket-Protocol']
    except KeyError:
        logging.error(
            "Client hasn't requested any Subprotocol. Closing Connection"
        )
        return await websocket.close()
    if websocket.subprotocol:
        logging.info("Protocols Matched: %s", websocket.subprotocol)
    else:
        # In the websockets lib if no subprotocols are supported by the
        # client and the server, it proceeds without a subprotocol,
        # so we have to manually close the connection.
        logging.warning('Protocols Mismatched | Expected Subprotocols: %s,'
                        ' but client supports  %s | Closing connection',
                        websocket.available_subprotocols,
                        requested_protocols)
        return await websocket.close()

    charge_point_id = path.strip('/')
    cp = ChargePoint(charge_point_id, websocket)

    await cp.start()


async def main():
    server = await websockets.serve(
        on_connect,
        '0.0.0.0',
        8080,
        subprotocols=['ocpp1.6']
    )

    logging.info("Server Started listening to new connections...")
    await server.wait_closed()


if __name__ == "__main__":
    # asyncio.run() is used when running this example with Python >= 3.7v
    asyncio.run(main())