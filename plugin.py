##           HomeWizard Wi-Fi Energy Socket Plugin
##
##           Author:         Eraser
##           Version:        1.0.0
##           Last modified:  28-05-2023
##
"""
<plugin key="HomeWizardEnergySocket" name="HomeWizard Wi-Fi Energy Socket" author="Eraser" version="1.0.0" externallink="https://www.homewizard.com/energy-socket/">
    <description>
        
    </description>
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="127.0.0.1" />
        <param field="Port" label="Port" width="200px" required="true" default="80" />
        <param field="Mode1" label="Data interval" width="200px">
            <options>
                <option label="10 seconds" value="10"/>
                <option label="20 seconds" value="20"/>
                <option label="30 seconds" value="30"/>
                <option label="1 minute" value="60" default="true"/>
                <option label="2 minutes" value="120"/>
                <option label="3 minutes" value="180"/>
                <option label="4 minutes" value="240"/>
                <option label="5 minutes" value="300"/>
            </options>
        </param>
        <param field="Mode2" label="State interval" width="200px">
            <options>
                <option label="10 seconds" value="10"/>
                <option label="20 seconds" value="20"/>
                <option label="30 seconds" value="30"/>
                <option label="1 minute" value="60" default="true"/>
                <option label="2 minutes" value="120"/>
                <option label="3 minutes" value="180"/>
                <option label="4 minutes" value="240"/>
                <option label="5 minutes" value="300"/>
            </options>
        </param>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
import json
import urllib
import urllib.request

class BasePlugin:
    #Plugin variables
    pluginInterval = 10     #in seconds
    dataInterval = 60       #in seconds
    stateInterval = 60      #in seconds
    dataIntervalCount = 0
    stateIntervalCount = 0
    LastSwitchState = ""
    
    #Homewizard Energy Socket variables
    wifi_strength = -1              #: [Number] De sterkte van het Wi-Fi signaal in %
    total_power_import_t1_kwh = -1  #: [Number] De stroom afname meterstand voor tarief 1 in kWh
    total_power_export_t1_kwh = -1  #: [Number] De stroom teruglevering meterstand voor tarief 1 in kWh
    active_power_w = -1             #: [Number] Het huidig gebruik van alle fases gecombineerd in Watt
    active_power_l1_w = -1          #: [Number] Het huidig gebruik voor fase 1 in Watt (indien van toepassing)
    
    #Calculated variables
    total_power = 0                 #: Het totale gecombineerde vermogen.
    import_active_power_w = 0       #: Het huidig vermogen wat momenteel van het net wordt geimporteerd.
    export_active_power_w = 0       #: Het huidig vermogen wat momenteel naar het net wordt geexporteerd.
    
    #Device ID's
    active_power_id = 101
    switch_id = 130
    wifi_signal_id = 140
    
    def onStart(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
            DumpConfigToLog()
        
        # If data interval between 10 sec. and 5 min.
        if 10 <= int(Parameters["Mode1"]) <= 300:
            self.dataInterval = int(Parameters["Mode1"])
        else:
            # If not, set to 60 sec.
            self.dataInterval = 60
            
        # If data interval between 10 sec. and 5 min.
        if 10 <= int(Parameters["Mode2"]) <= 300:
            self.stateInterval = int(Parameters["Mode2"])
        else:
            # If not, set to 60 sec.
            self.stateInterval = 60
            
        try:
            if ( self.switch_id not in Devices ):
                Domoticz.Device(Name="Energy Socket Switch",  Unit=self.switch_id, Type=244, Subtype=73, Switchtype=0).Create()
        except:
            Domoticz.Error("Failed to create device id " + str(self.switch_id))
            
        # Start the heartbeat
        Domoticz.Heartbeat(self.pluginInterval)
        
        return True
        
    def onConnect(self, Status, Description):
        return True

    def onMessage(self, Data, Status, Extra):
        if ( Extra == "data" ):
            try:
                Domoticz.Debug("Reading values from data")
                
                self.wifi_strength = Data['wifi_strength']
                self.total_power_import_t1_kwh = int(Data['total_power_import_t1_kwh'] * 1000)
                self.total_power_export_t1_kwh = int(Data['total_power_export_t1_kwh'] * 1000)
                self.active_power_w = int(Data['active_power_w'])
                
                if ( 'active_power_l1_w' in Data ): self.active_power_l1_w = int(Data['active_power_l1_w'])
                    
                Domoticz.Debug("Calculating values")
                
                self.total_power = self.total_power_import_t1_kwh - self.total_power_export_t1_kwh
                
                if ( self.active_power_w >= 0 ):
                    self.import_active_power_w = self.active_power_w
                    self.export_active_power_w = 0
                else:
                    self.import_active_power_w = 0
                    self.export_active_power_w = self.active_power_w * -1
                    
                #------- Device updates -------
                try:
                    if ( self.active_power_id not in Devices ):
                        Domoticz.Device(Name="Power usage",  Unit=self.active_power_id, Type=243, Subtype=29).Create()
                        
                    UpdateDevice(self.active_power_id, 0, numStr(self.active_power_w) + ";" + numStr(self.total_power), True)
                except:
                    Domoticz.Error("Failed to update device id " + str(self.active_power_id))
                    
                try:
                    if ( self.wifi_signal_id not in Devices ):
                        Domoticz.Device(Name="Wifi signal",  Unit=self.wifi_signal_id, TypeName="Percentage").Create()
                        
                    UpdateDevice(self.wifi_signal_id, 0, numStr(self.wifi_strength), True)
                except:
                    Domoticz.Error("Failed to update device id " + str(self.wifi_signal_id))
            except:
                Domoticz.Error("Failed to handle data response")
                return
            
        if ( Extra == "state" ):
            try:
                Domoticz.Debug("Reading values from state")
                
                if ( 'power_on' in Data ):
                    PowerState = 'Off'
                    
                    Domoticz.Debug("Handling power_on response")
                    if ( str(Data['power_on']) == 'True' ):
                        if ( self.LastSwitchState != "On" ):
                            self.LastSwitchState = "On"
                            UpdateDevice(self.switch_id, 1, "On", True)
                    else:
                        if ( self.LastSwitchState != "Off" ):
                            self.LastSwitchState = "Off"
                            UpdateDevice(self.switch_id, 0, "Off", True)
            except:
                Domoticz.Error("Failed to handle state response")
                return
            
        return True
                    
    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level) + ", Hue: " + str(Hue))
        
        if ( Unit == self.switch_id):
            if ( Command == "On"):
                Domoticz.Debug("Toggle switch On")
                self.toggleOn()
            else:
                Domoticz.Debug("Toggle switch Off")
                self.toggleOff()
        
        return True

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        #Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)
        return

    def onHeartbeat(self):
        self.dataIntervalCount += self.pluginInterval
        self.stateIntervalCount += self.pluginInterval
        
        if ( self.dataIntervalCount >= self.dataInterval ):
            #------- Collect data -------
            self.dataIntervalCount = 0
            self.readData()
            
        if ( self.stateIntervalCount >= self.stateInterval ):
            #------- Read status -------
            self.stateIntervalCount = 0
            self.readState()
        
        return

    def onDisconnect(self):
        return

    def onStop(self):
        #Domoticz.Log("onStop called")
        return True

    def readData(self):
        try:
            APIdata = urllib.request.urlopen("http://" + Parameters["Address"] + ":" + Parameters["Port"] + "/api/v1/data").read()
        except:
            Domoticz.Error("Failed to communicate with Energy Socket at ip " + Parameters["Address"] + " with port " + Parameters["Port"])
            return False
        
        try:
            APIjson = json.loads(APIdata.decode("utf-8"))
        except:
            Domoticz.Error("Failed converting API data to JSON")
            return False
            
        try:
            self.onMessage(APIjson, "200", "data")
        except:
            Domoticz.Error("onMessage failed with some error")
            return False
            
    def readState(self):
        try:
            APIdata = urllib.request.urlopen("http://" + Parameters["Address"] + ":" + Parameters["Port"] + "/api/v1/state").read()
        except:
            Domoticz.Error("Failed to communicate with Energy Socket at ip " + Parameters["Address"] + " with port " + Parameters["Port"])
            return False
        
        try:
            APIjson = json.loads(APIdata.decode("utf-8"))
        except:
            Domoticz.Error("Failed converting API data to JSON")
            return False
            
        try:
            self.onMessage(APIjson, "200", "state")
        except:
            Domoticz.Error("onMessage failed with some error")
            return False
    
    def putState(self,Data):
        try:
            Domoticz.Debug("Creating PUT request")
            req = urllib.request.Request(url='http://' + Parameters["Address"] + ':' + Parameters['Port'] + '/api/v1/state', data=Data, method='PUT')
            Domoticz.Debug("Sending PUT request")
            APIdata = urllib.request.urlopen(req).read()
            Domoticz.Debug("PUT request has been send")
        except:
            Domoticz.Error("Failed to communicate with Energy Socket at ip " + Parameters["Address"] + " with port " + Parameters["Port"])
            return False
            
        try:
            Domoticz.Debug("Response data: " + APIdata.decode("utf-8"))
            APIjson = json.loads(APIdata.decode("utf-8"))
        except:
            Domoticz.Error("Failed converting API data to JSON")
            return False
            
        try:
            self.onMessage(APIjson, "200", "state")
        except:
            Domoticz.Error("onMessage failed with some error")
            return False
    
    def toggleOn(self):
        try:
            Data = b'{ "power_on": true }'
            self.putState(Data)
        except:
            Domoticz.Error("Failed to turn Energy Socket at ip " + Parameters["Address"] + " with port " + Parameters["Port"] + " On")
            return False
    
    def toggleOff(self):
        try:
            Data = b'{ "power_on": false }'
            self.putState(Data)
        except:
            Domoticz.Error("Failed to turn Energy Socket at ip " + Parameters["Address"] + " with port " + Parameters["Port"] + " Off")
            return False
    
global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Status, Description):
    global _plugin
    _plugin.onConnect(Status, Description)

def onMessage(Data, Status, Extra):
    global _plugin
    _plugin.onMessage(Data, Status, Extra)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect():
    global _plugin
    _plugin.onDisconnect()

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions
def isNumber(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
        
def numStr(s):
    try:
        return str(s).replace('.','')
    except:
        return "0"

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

def UpdateDevice(Unit, nValue, sValue, AlwaysUpdate=False, SignalLevel=12):    
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if ((Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or (AlwaysUpdate == True)):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue), SignalLevel=SignalLevel)
            Domoticz.Debug("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
    return
