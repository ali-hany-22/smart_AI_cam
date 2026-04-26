/*
 * ================================================================
 *  ROPTICS AI - ESP32 Pan Servo Controller
 *  Servo: MG996R (Pan only - يمين/شمال)
 *  Communication: Serial (USB) @ 115200 baud
 *  Commands from Python:
 *    'L'     → Move Left
 *    'R'     → Move Right
 *    'S'     → Stop (Hold position)
 *    'SX90'  → Set Pan to exact angle (0-180)
 * ================================================================
 */
#include <ESP32Servo.h>

// ================= PIN CONFIG =================
#define SERVO_PAN_PIN   18     

// ================= SERVO SETTINGS =================
#define PAN_MIN         0       
#define PAN_MAX         180     
#define PAN_CENTER      90      
#define PAN_STEP        3       
#define MOVE_DELAY_MS   15     

// ================= MG996R PULSE WIDTH =================
#define SERVO_MIN_US    500
#define SERVO_MAX_US    2500

// ================= STATE =================
Servo panServo;

int   panAngle    = PAN_CENTER;   
char  currentCmd  = 'S';          
bool  moving      = false;

// ================= SETUP =================
void setup() {
    Serial.begin(115200);

    ESP32PWM::allocateTimer(0);
    panServo.setPeriodHertz(50);                          // 50Hz standard servo
    panServo.attach(SERVO_PAN_PIN, SERVO_MIN_US, SERVO_MAX_US);

    panServo.write(PAN_CENTER);
    delay(500);

    Serial.println("✅ Roptics ESP32 Pan Controller Ready");
    Serial.println("Commands: L=Left | R=Right | S=Stop | SX[angle]=Set Angle");
}

// ================= LOOP =================
void loop() {
    if (Serial.available() > 0) {
        String input = Serial.readStringUntil('\n');
        input.trim();
        processCommand(input);
    }

    executeMovement();

    delay(MOVE_DELAY_MS);
}

// ================= PROCESS COMMAND =================
void processCommand(String cmd) {
    if (cmd.length() == 0) return;

    if (cmd == "L") {
        currentCmd = 'L';
        moving     = true;
        Serial.println("← Moving Left");
    }

    else if (cmd == "R") {
        currentCmd = 'R';
        moving     = true;
        Serial.println("→ Moving Right");
    }

    else if (cmd == "S") {
        currentCmd = 'S';
        moving     = false;
        Serial.print("■ Stopped at angle: ");
        Serial.println(panAngle);
    }

    else if (cmd.startsWith("SX")) {
        int angle = cmd.substring(2).toInt();
        angle     = constrain(angle, PAN_MIN, PAN_MAX);
        setAngle(angle);
        currentCmd = 'S';
        moving     = false;
        Serial.print("Set to angle: ");
        Serial.println(angle);
    }

    // أمر مجهول
    else {
        Serial.print("Unknown command: ");
        Serial.println(cmd);
    }
}

// ================= EXECUTE MOVEMENT =================
void executeMovement() {
    if (!moving) return;

    if (currentCmd == 'L') {
        panAngle -= PAN_STEP;
        if (panAngle <= PAN_MIN) {
            panAngle = PAN_MIN;
            moving   = false;      
            Serial.println("Left limit reached");
        }
        panServo.write(panAngle);
    }

    else if (currentCmd == 'R') {
        panAngle += PAN_STEP;
        if (panAngle >= PAN_MAX) {
            panAngle = PAN_MAX;
            moving   = false;       
            Serial.println("Right limit reached");
        }
        panServo.write(panAngle);
    }
}

// ================= SET ANGLE DIRECTLY =================
void setAngle(int angle) {
    int step = (angle > panAngle) ? 1 : -1;

    while (panAngle != angle) {
        panAngle += step;
        panAngle  = constrain(panAngle, PAN_MIN, PAN_MAX);
        panServo.write(panAngle);
        delay(8);   
    }
}
