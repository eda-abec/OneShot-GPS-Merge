SCRIPT = os_gps_merge.py
INTERPRETER = python3
OUTPUT = stored_gps.csv

all: $(OUTPUT)

$(OUTPUT):
	$(INTERPRETER) $(SCRIPT) stored.csv wigle/WigleWifi_*.csv $(OUTPUT) -p pins/

benchmark:
	time $(INTERPRETER) $(SCRIPT) stored.csv wigle/WigleWifi_*.csv $(OUTPUT) -p pins/

clean:
	rm -f $(OUTPUT)

force: clean $(OUTPUT)
