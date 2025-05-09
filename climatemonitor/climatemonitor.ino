#include <DHT11.h> // Here we are using a third-party library
#define DHTPIN 2 // Define the pin connected to the DHT11 sensor
DHT11 dht(DHTPIN); // Create a DHT11 object and specify the pin
void setup() {
Serial.begin(115200); // Initialize serial communication
}
void loop() {
//delay(500); // Delay for 0.5 seconds
float humidity = dht.readHumidity(); // Read humidity value
float temperature = dht.readTemperature(); // Read temperature value
Serial.println("### Sending data to PC ###");
Serial.print("Humidity (%): ");
Serial.println(humidity); // Print humidity value
Serial.print("Temperature (C): ");
Serial.println(temperature); // Print temperature value
Serial.println("### End communication ###");
}