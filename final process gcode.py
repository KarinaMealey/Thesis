import time
from pymycobot.mycobot280 import MyCobot280

# Initialize robot
mc = MyCobot280('COM3', 115200)
time.sleep(0.5)
mc.set_fresh_mode(0)
mc.set_color(0, 255, 0)
time.sleep(0.5)

# initialize updated tool frame
mc.set_tool_reference([0, -118.7, 84, 0, 0, 0]) # DO NOT CHANGE, z should be around 80-84, depends on how much drooping
mc.set_end_type(1)
mc.set_reference_frame(0)
mc.set_gripper_value(100,1) # set gripper to open
time.sleep(0.5)

# send to initial position and extract coords
mc.send_coords([240,-30, 80, -180, 0, -90], 10,1)
#get_coords = mc.get_coords()
draw_speed = 1 # can test different values, lower speeds have best synchronicity with robot
gripper_position = 78 # starting around 70-80 usually works best
gripper_speed = 100 # 100 is SLOWEST speed
time.sleep(5)

### this setup works pretty well! dont change.

# gripper close function
def gripper_close():
    global gripper_position

    if gripper_position > 0:
        #time.sleep(0.2) # uncomment and change if needed for synch
        mc.set_gripper_state(1, 100)  # 1 = closed state, 0 = open, 100 = speed
    # checks to see if robot has stopped moving(reached coordinate)
        time.sleep(0.3) # wrks with speed 1, modify this if needed for better synchronicity
        while mc.is_moving(): # check to see if robot is still moving
            time.sleep(0.01)
        mc.set_gripper_state(254, 1)  # 254 = stop gripper motion, when robot stops
        gripper_position = mc.get_gripper_value()

# gripper stop closing function
def gripper_stop():
    mc.set_gripper_state(254, 1)  # 254 = stop gripper movement

# Parse G-code
def process_gcode(file_path):
    get_coords = mc.get_coords()
    last_coords = [get_coords[0], get_coords[1], get_coords[2], -180, 0, -90] # last 3 must match above, input directly to reduce error from innacuracies
    data_coords = []

    with open(file_path, 'r', encoding='utf-8-sig') as file:
        for line in file:
            command = line.strip()

            # Skip empty lines, comments, and non-G0,G1 lines
            if not command or command.startswith(";"):
                continue
            if not (command.startswith("G0") or command.startswith("G1")):
                continue

            coords = last_coords[:]
            x, y, z = None, None, None
            parts = command.split()
            is_extrusion = any(part.startswith(("E", "e")) for part in parts)

            # extract cordinate values
            for part in parts[1:]:
                if (part.startswith("X") or part.startswith("x")) and len(part) > 1:
                    try:
                        x = float(part[1:])
                    except ValueError:
                        pass
                elif (part.startswith("Y") or part.startswith("y")) and len(part) > 1:
                    try:
                        y = float(part[1:])
                    except ValueError:
                        pass
                elif (part.startswith("Z") or part.startswith("z")) and len(part) > 1:
                    try:
                        z = float(part[1:])
                    except ValueError:
                        pass
                elif part.startswith("F"):
                    continue  # Skip feed rate values

            # Add extracted value to coords list, use prev value if line does not contain new one
            ### ADD X offset from build plate here
            coords[0] = (x + 217.4) if x is not None else last_coords[0]
            coords[1] = y if y is not None else last_coords[1]
            #### ADD Z offset from build plate here!!
            coords[2] = (z + 80 + 0.015 * abs(coords[0])) if z is not None else last_coords[2]

            # Remove duplicate coords
            if coords[:3] != last_coords[:3]:
                command_type = "G1_E" if is_extrusion else "G1_noE" #set command type
                data_coords.append((coords, command_type)) # add coords and commmand type to command list
                last_coords = coords

    # Output command list
    print("Parsed coords:")
    for coords, cmd in data_coords:
        print(cmd, coords)

    return data_coords

# File selection
# add in new Gcode files here
type = int(input('Please input 1-4（1-UltraCur3D 1 layer 2-gripper test 3-UltraCur3D full print 4-quit）:'))
if type in [1, 2, 3]:
    if type == 1:
        file_path = 'UltraCur3D_50x50mm_1layer.gcode.txt'
    elif type == 2:
        file_path = 'gripper_test.nc'
    elif type == 3:
        file_path = 'UltraCur3D_50x50mm.gcode'

    coords_data = process_gcode(file_path) # run process Gcode func for selected file

    # Main execution loop
    for coords, command_type in coords_data:
        if command_type == "G1_E":
            #print(f"Printing motion to {coords[:3]}")
            mc.send_coords(coords, draw_speed, 1)
            gripper_close()
            mc.set_color(0, 0, 255)  # blue = print, not necessary

        elif command_type == "G1_noE":
            mc.send_coords(coords, draw_speed, 1)
            mc.set_color(0, 255, 0) # green = no print, not necessary

        while mc.is_moving(): # pause between sending new coords
            time.sleep(0.05)

elif type == 4: # exit G-code selection
    exit(0)