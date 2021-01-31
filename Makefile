SCRIPT = os_gps_merge.py
INTERPRETER = python3

# output files
OUTPUT = stored_gps.csv
OUTPUT_PINS = stored_pins.csv
UNMATCHED = unmatched.csv
OUTPUT_KML = stored_gps.kml
OUTPUT_PINS_KML = stored_pins.kml


# take all possible inputs and generate all available outputs
all:
	$(INTERPRETER) $(SCRIPT) stored.csv wigle/WigleWifi_*.csv $(OUTPUT) -p pins/ --pins-output stored_pins.csv -k stored_gps.kml --kml-pins stored_pins.kml -u unmatched.csv

# basic usage
$(OUTPUT):
	$(INTERPRETER) $(SCRIPT) stored.csv wigle/WigleWifi_*.csv $(OUTPUT)

benchmark:
	time $(INTERPRETER) $(SCRIPT) stored.csv wigle/WigleWifi_*.csv $(OUTPUT)

# remove all output files
clean:
	rm -f $(OUTPUT) $(OUTPUT_PINS) $(UNMATCHED) $(OUTPUT_KML) $(OUTPUT_PINS_KML)

force: clean $(OUTPUT)
