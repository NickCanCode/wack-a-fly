def arm():

    # Initialize the touch sensor
    contact = False
    while not contact:

        #waiting for touch sensor to be pressed
        if touch_sensor.is_pressed:
            contact = True
            
        #arm up and down

            
    return contact

    

