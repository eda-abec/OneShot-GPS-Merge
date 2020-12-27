SCRIPT = os_gps_merge.py
INTERPRETER = python3
OUTPUT = stored_gps.csv

all: $(OUTPUT)

$(OUTPUT):
	$(INTERPRETER) $(SCRIPT) stored.csv WigleWifi_*.csv $(OUTPUT)

benchmark:
	time $(INTERPRETER) $(SCRIPT) stored.csv WigleWifi_*.csv $(OUTPUT)

# needs more work
#matched: $(OUTPUT)
#	diff $(OUTPUT) stored.csv

clean:
	rm -f $(OUTPUT)
