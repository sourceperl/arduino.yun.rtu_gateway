/*
  Test of a Yun Rev 1 with Akene shield (Sigfox)

  Since SoftwareSerial on leornado don't run on D4/D5 standard pin we use D11/D10 instead

  OpenWRT (Linux) send command to the bridge (/dev/ttyATH0) to ATMega 32U4

  We need to disable "ttyATH0::askfirst:/bin/ash --login" in /etc/inittab with a comment # in front.
  This disable OpenWRT linux command processor. With this,  we are able to use /dev/ttyATH0 directly
  between python and ATMega 32U4.

  Add python script "python /root/modbus2sigfox.py" in /etc/rc.local for periodic sigfox payload product.
  In rc.local uncomment "echo 0 > /proc/sys/kernel/printk"

*/

// from https://github.com/Snootlab/Akeru
#include <Akeru.h>
// from https://github.com/arkhipenko/TaskScheduler
#include <TaskScheduler.h>

// some const
// serial commands
#define CMD_TIMEOUT         10E3
#define MAX_CMD_SIZE        64
/*   Snootlab device | TX  | RX
               Akeru | D4  | D5
               Akene | D5  | D4
               Custom| D11 | D10 */
#define MODEM_TX 11
#define MODEM_RX 10

// some structs
struct CmdStream {
    Stream &serial;
    String rx_buffer;
    unsigned long t_last_byte;
};

// some vars
String sigfox_pld = "";
Akeru akeru(MODEM_RX, MODEM_TX);
Scheduler runner;
struct CmdStream CmdSerial = {Serial, "", 0};
struct CmdStream CmdSerial1 = {Serial1, "", 0};

// some prototypes
void task_serial_command();
void task_led_alive();
void task_sigfox_sender();

// some tasks
Task t_cmd(1, TASK_FOREVER, &task_serial_command, &runner, true);
Task t_alive(1 * TASK_SECOND, TASK_FOREVER, &task_led_alive, &runner, true);
Task t_send(15 * TASK_MINUTE, TASK_FOREVER, &task_sigfox_sender, &runner, true);

// some functions
void command_processor(CmdStream &cs) {
  // check command
  while (cs.serial.available() > 0) {
    // receive loop
    while (true) {
      int inByte = cs.serial.read();
      // no more data
      if (inByte == -1)
        break;
      // reset command buffer if the last rx is too old
      if (millis() - cs.t_last_byte > CMD_TIMEOUT)
        cs.rx_buffer = "";
      cs.t_last_byte = millis();
      // add data to s_cmd
      cs.rx_buffer += (char) inByte;
      // limit size to MAX_CMD_SIZE
      if (cs.rx_buffer.length() > MAX_CMD_SIZE)
        cs.rx_buffer.remove(0, cs.rx_buffer.length() - MAX_CMD_SIZE);
      // pause receive loop if \n occur
      if (inByte == '\n')
        break;
    }
    // skip command not ended with "\r\n"
    if (! cs.rx_buffer.endsWith("\r\n"))
      break;
    // remove leading and trailing \r\n, force case
    cs.rx_buffer.trim();
    cs.rx_buffer.toUpperCase();
    // check for command argument (cmd [space char] [arg])
    int index_space  = cs.rx_buffer.indexOf(" ");
    String s_arg = "";
    String s_cmd = cs.rx_buffer;
    if (index_space != -1) {
      s_cmd = cs.rx_buffer.substring(0, index_space);
      s_arg = cs.rx_buffer.substring(index_space + 1);
      s_arg.trim();
    }
    // check command
    if (s_cmd.equals("GET_PLD")) {
      cs.serial.print(F("sigfox payload is "));
      cs.serial.println(sigfox_pld);
    }
    else if (s_cmd.equals("SET_PLD")) {
      sigfox_pld = s_arg;
      cs.serial.print(F("sigfox payload set at "));
      cs.serial.println(sigfox_pld);
    }
    // reset for next one
    cs.rx_buffer = "";
  }
}

// define tasks
void task_serial_command() {
  // process command on USB CDC and serial bridge
  command_processor(CmdSerial);
  command_processor(CmdSerial1);
}

void task_led_alive() {
  digitalWrite(LED_BUILTIN, ! digitalRead(LED_BUILTIN));
}

void task_sigfox_sender() {
  // send sigfox message
  if (akeru.sendPayload(sigfox_pld)) {
    Serial.print(F("SUCCESS: sigfox message sent payload "));
    Serial.println(sigfox_pld);
  } else {
    Serial.print(F("ERROR: sigfox message sent payload "));
    Serial.println(sigfox_pld);
  }
}

void setup() {
  // IO init
  pinMode(LED_BUILTIN, OUTPUT);
  // init serial USB CDC
  Serial.begin(9600);
  //while (!Serial);
  // init serial Linux <-> ATMega 32U4
  Serial1.begin(9600);
  // Check TD1208 communication
  if (!akeru.begin()) {
    Serial.println("TD1208 KO");
    while (true);
  }
  // init job for task sheduler
  // run sigfox sender task 2 minutes after startup
  t_send.delay(2 * TASK_MINUTE);
}

void loop() {
  // scheduler handler
  runner.execute();
}

