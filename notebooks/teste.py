import ewelink
from ewelink import Client, DeviceOffline

@ewelink.login('poposa5014', 'nielsen.tekla@gmail.com')
async def main(client: Client):
    print(client.region)
    print(client.user.info)
    print(client.devices)
    
    device = client.get_device('10013abe9c') #single channel device
    # device2 = client.get_device('10007fgah9') #four channel device
    
    print(device.params) 
        #Raw device specific properties 
        #can be accessed easily like: device.params.switch or device.params['startup'] (a subclass of dict)

    print(device.state)
    print(device.created_at)
    print("Brand Name:", device.brand.name, "Logo URL:", device.brand.logo.url)
    print("Device online?", device.online)
    
    try:
        await device.off[0]()
    except DeviceOffline:
        print("Device is offline!")