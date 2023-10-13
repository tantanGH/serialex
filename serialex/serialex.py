import os
import argparse
import serial
import signal
import threading
import selectors

# abort flag (global)
g_abort_service = False

# wakeup pipe (global)
g_wakeup_write = None

# sigint handler
def sigint_handler(signum, frame):
  print("CTRL-C is pressed. Stopping the service.")
  global g_abort_service
  g_abort_service = True
  global g_wakeup_write
  os.write(g_wakeup_write, b'1')

# serial event handler
def serial_event_handler(source_serial_port, target_serial_port):
  global g_abort_service
  while g_abort_service is False:
    if source_serial_port.in_waiting > 0:
      data = source_serial_port.read_all()
      target_serial_port.write(data)

# service loop
def run_service(serial_device0, serial_device1, serial_baudrate):

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

      # pipe for select loop breaking
      wakeup_read, wakeup_write = os.pipe()

      # set sigterm handler
      global g_abort_service
      g_abort_service = False
      global g_wakeup_write
      g_wakeup_write = wakeup_write
      signal.signal(signal.SIGINT, sigint_handler)

      # thread for serial port 0
      th0 = threading.Thread(target=serial_event_handler, args=(serial_port0, serial_port1))
      th0.start()

      # thread for serial port 1
      th1 = threading.Thread(target=serial_event_handler, args=(serial_port1, serial_port0))
      th1.start()

      print(f"Started. (serial_device0={serial_device0}, serial_device1={serial_device1},baudrate={serial_baudrate})")

      # IO selector
      selector = selectors.DefaultSelector()
      selector.register(wakeup_read, selectors.EVENT_READ)

      # main loop
      try:
        while g_abort_service is False:
          events = selector.select()
          for key, mask in events:
            if key.fileobj == wakeup_read:
              os.read(wakeup_read, 1)
      except Exception as e:
        print(e)
      finally:
        th0.join()
        th1.join()
        serial_port0.close()
        serial_port1.close()
        selector.close()
        os.close(wakeup_read)
        os.close(wakeup_write)

      print("Stopped.")

def main():

  parser = argparse.ArgumentParser()
  parser.add_argument("serial_device0", help="serial device#0")
  parser.add_argument("serial_device1", help="serial device#1")
  parser.add_argument("-s", "--baudrate", help="baud rate (default:9600)", type=int, default=9600)
 
  args = parser.parse_args()

  return run_service(args.serial_device0, args.serial_device1, args.baudrate)

if __name__ == "__main__":
  main()
