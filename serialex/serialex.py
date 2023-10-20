import os
import argparse
import serial
import signal
import threading

# abort flag (global)
g_abort_service = False

# sigint handler
def sigint_handler(signum, frame):
  print("CTRL-C is pressed. Stopping the service.")
  global g_abort_service
  g_abort_service = True

# serial event handler
def serial_event_handler(source_serial_port, target_serial_port, verbose):
  global g_abort_service
  while g_abort_service is False:
    if source_serial_port.in_waiting > 0:
      data = source_serial_port.read_all()
      if len(data) > 0:
        target_serial_port.write(data)
        if verbose:
          print(data, end="", flush=True)

# service loop
def run_service(serial_device0, serial_device1, serial_baudrate, verbose):

  # open serial port0
  with serial.Serial(serial_device0, serial_baudrate,
                     bytesize = serial.EIGHTBITS,
                     parity = serial.PARITY_NONE,
                     stopbits = serial.STOPBITS_ONE,
                     timeout = 120,
                     xonxoff = False,
                     rtscts = False,
                     dsrdtr = False ) as serial_port0:

    with serial.Serial(serial_device1, serial_baudrate,
                      bytesize = serial.EIGHTBITS,
                      parity = serial.PARITY_NONE,
                      stopbits = serial.STOPBITS_ONE,
                      timeout = 120,
                      xonxoff = False,
                      rtscts = False,
                      dsrdtr = False ) as serial_port1:

      # set sigterm handler
      global g_abort_service
      g_abort_service = False
      signal.signal(signal.SIGINT, sigint_handler)

      # thread for serial port 0
      th0 = threading.Thread(target=serial_event_handler, args=(serial_port0, serial_port1, verbose == 0 or verbose == 2))
      th0.start()

      # thread for serial port 1
      th1 = threading.Thread(target=serial_event_handler, args=(serial_port1, serial_port0, verbose == 1 or verbose == 2))
      th1.start()

      print(f"Started. (serial_device0={serial_device0}, serial_device1={serial_device1},baudrate={serial_baudrate})")

      th0.join()
      th1.join()

      serial_port0.close()
      serial_port1.close()

      print("Stopped.")

def main():

  parser = argparse.ArgumentParser()
  parser.add_argument("serial_device0", help="serial device#0")
  parser.add_argument("serial_device1", help="serial device#1")
  parser.add_argument("-s", "--baudrate", help="baud rate (default:9600)", type=int, default=9600)
  parser.add_argument("-v", "--verbose", help="verbose mode", type=int, default=-1)
 
  args = parser.parse_args()

  return run_service(args.serial_device0, args.serial_device1, args.baudrate, args.verbose)

if __name__ == "__main__":
  main()
