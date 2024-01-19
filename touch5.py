import netman
import utime
import rp2
import machine
from machine import Pin
import time
import urequests
import ujson
import gc
publish_key='pub-c-----'
subscribe_key='sub-c-----'
pubnub_api_endpoint=f'https://ps.pndsn.com/publish/{publish_key}/{subscribe_key}/0/hello_world/0'
payload1={"title":"greetings","description":"mute"}
payload2={"title":"greetings","description":"unmute"}
country='SG'
ssid=''
password=''
wifi_connection=netman.connectWiFi(ssid,password,country)
led=machine.Pin('LED',machine.Pin.OUT)
led.value(1)
utime.sleep(1)
led.value(0)
utime.sleep(0.4)
led_green=Pin(27,Pin.OUT,Pin.PULL_DOWN)
led_green.high()
led_blue=Pin(26,Pin.OUT,Pin.PULL_DOWN)
led_blue.high()
led_red=Pin(28,Pin.OUT,Pin.PULL_DOWN)
led_red.high()
machine.freq(125_000_000)
device=None
@rp2.asm_pio(set_init=[rp2.PIO.OUT_LOW])
def capsense():
	mov(isr,null)
	set(y,1)
	in_(y,1)
	in_(null,20)
	mov(y,isr)
	mov(x,invert(null))
	label('resample')
	set(pindirs,0)
	label('busy')
	jmp(pin,'high')
	jmp(y_dec,'busy')
	jmp('done')
	label('high')
	set(pindirs,1)
	set(pins,0)
	jmp(y_dec,'dec1')
	jmp('done')
	label('dec1')
	jmp(y_dec,'dec2')
	jmp('done')
	label('dec2')
	jmp(y_dec,'dec3')
	jmp('done')
	label('dec3')
	jmp(y_dec,'dec4')
	jmp('done')
	label('dec4')
	jmp(y_dec,'dec5')
	jmp('done')
	label('dec5')
	jmp(x_dec,'resample')
	label('done')
	mov(isr,x)
	push(block)
u32max=const((1<<32)-1)
class Channel:
	def __init__(self,pin,sm):
		self.warmup=100
		self.touch_start_time=None
		self.touch_event_printed=False
		self.touch_start_time1=None
		self.touch_event_printed1=False
		self.counter=0
		self.toggle_status=False
		self.level=0
		self.level_lo=u32max
		self.level_hi=0
		machine.Pin(pin,machine.Pin.IN,machine.Pin.PULL_UP)
		self.state_machine=rp2.StateMachine(sm,capsense,freq=125_000_000,set_base=machine.Pin(pin),jmp_pin=machine.Pin(pin))
		self.state_machine.active(1)
	def __enter__(self):
		return self
	def __exit__(self,exc_type,exc_value,traceback):
		self.active(0)
	def active(self,active):
		self.state_machine.active(active)
	@micropython.native
	def update(self):
		if self.state_machine.rx_fifo()>0:
			for f in range(5):
				level=u32max-self.state_machine.get()
				if self.state_machine.rx_fifo()==0:
					break
			if self.warmup>0:
				self.warmup-=1
			else:
				self.level_lo=min(level,self.level_lo)
				self.level_hi=max(level,self.level_hi)
			window=self.level_hi-self.level_lo
			if window>64:
				self.level=1-((level-self.level_lo)/window)
				gc.collect()
				if self.level>0.5:
					self.touch_start_time1=None
					self.touch_event_printed1=False
					if self.touch_start_time is None:
						self.touch_start_time=time.ticks_ms()
						self.touch_event_printed=False
					else:
						touch_duration=time.ticks_diff(time.ticks_ms(),self.touch_start_time)
						if touch_duration>=500 and not self.touch_event_printed:
							print("Touch event lasting for 3 seconds detected!")
							led.value(1)
							led_green.low()
							led_blue.high()
							led_red.high()
							self.counter+=1
							if self.counter==2:
								print("Explode")
								self.toggle_status= not self.toggle_status
								if(self.toggle_status):
									payload=payload1
								else:
									payload=payload2
								json_payload=ujson.dumps(payload)
								response=urequests.post(pubnub_api_endpoint,data=json_payload)
								led_green.high()
								led_blue.high()
								led_red.high()
								gc.collect()
							self.touch_event_printed=True
				else:
					self.touch_start_time=None
					self.touch_event_printed=False
					led.value(0)
					led_green.high()
					led_blue.high()
					led_red.high()
					if self.touch_start_time1 is None:
						self.touch_start_time1=time.ticks_ms()
						self.touch_event_printed1=False
					else:
						touch_duration1=time.ticks_diff(time.ticks_ms(),self.touch_start_time1)
						if touch_duration1>=1000 and not self.touch_event_printed1:
							print("Not touch event lasting for 3 seconds detected!")
							self.counter=0
							self.touch_event_printed1=True
class Device:
	def __init__(self,pin):
		self.channels=[Channel(pin,0)]
	def __enter__(self):
		return self
	def __exit__(self,exc_type,exc_value,traceback):
		for c in self.channels:
			c.active(0)
	def update(self):
		for c in self.channels:
			c.update()
	def level(self,channel):
		return self.channels[channel].level
def main():
	bars=['⠀','⡀','⣀','⣄','⣤','⣦','⣶','⣷','⣿']
	with(Device(0))as touch:
		while True:
			touch.update()
			gc.collect()
			time.sleep(0.01)
if __name__=='__main__':
	main()
