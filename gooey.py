import io
import operator
import yuv2rgb
import atexit
import pygame
import pygame.font
import os
import os.path
import picamera
import yuv2rgb

# CLASSES ------------------------------------------------------
class MainMenuItem:#Basic superclass for anything shoved into the mainmenu.
    def __init__(self, text):
      self.text=text
      self.img  = gooeyfont.render(text,False, fontColor)
      self.index = 0
      self.min = 0
      self.max = 0
      self.action=None #Action for enter key press
      self.change=None #Action for value change
      
    def draw(self):
      return
      
    def setAction(self,fun):#Set up to be easily declared in one line
      self.action=fun
      return self
      
    def setChange(self,fun):
      self.change=fun;
      return self
      
    def setIndex(self,newindex):#You could set index directly for many things, but this keeps it sane(Calls change method with self as parameter)
      self.index=newindex
      if newindex>self.max:
        self.index=self.min
      elif newindex<self.min:
        self.index=self.max
      if self.change!=None:
        self.change(self)
      return self
      
class SubSpinner(MainMenuItem):#A main menu item that contains a changable value.
    def __init__(self,text,minimum,maximum,value):
      MainMenuItem.__init__(self,text)
      self.min=minimum
      self.max=maximum
      self.index=value
      self.img  = gooeyfont.render(self.text+str(self.index),False, fontColor)
      
    def setIndex(self,newindex):
      MainMenuItem.setIndex(self,newindex)
      self.img  = gooeyfont.render(self.text+str(self.index),False, fontColor)
      return self
      

class SubMenu(MainMenuItem):#A main menu item that contains a sub menu
    
    def __init__(self, text, *args):
      MainMenuItem.__init__(self, text)
      self.children = args
      self.max = len(args)-1

    def getSelectedItem(self):
      return self.children[self.index]
    
    def draw(self):    #Called to draw the submenu at 0,0
      if len(self.children)>0:
        y=0
        i=0
        for child in self.children:
          if i==self.index:
            screen.fill(selectedBGColor,pygame.Rect(0,y,child.img.get_width(),child.img.get_height()))
          else:
            screen.fill(unselBGColor,pygame.Rect(0,y,child.img.get_width(),child.img.get_height()))
          screen.blit(child.img,(0,y))
          y+=gooeyfont.get_linesize()+1
          if y>screenHeight-2*(gooeyfont.get_linesize()+1): #Prevent drawing over menu
            return
          i+=1
          
class SubDictMenu(SubMenu):#For passing the modes arrays to for convenience since they don't need actions
    def __init__(self,text,dictionary):
      SubMenu.__init__(self,text)
      self.children=[]
      for item in sorted(dictionary.items(), key=operator.itemgetter(1)):
        self.children.append(MenuItem(item[0]))
      self.max=len(self.children)-1

        
class MenuItem:#Menu items to be passed into subMenu objects for the main menu
        
    def __init__(self, text, action=None):
      self.text=text
      self.img  = gooeyfont.render(text,False, fontColor)
      self.action=action
      
    def setAction(self,fun):
      self.action=fun
      return self
      
# METH ---------------------------------------------------------
def drawMenu():
  i=0
  x=0
  #for item in mainMenu:
  for it in range(menuSelection,len(mainMenu)):
    item=mainMenu[it]
    if it==menuSelection:
      screen.fill(selectedBGColor,pygame.Rect(x,screenHeight-gooeyfont.get_linesize(),item.img.get_width(),item.img.get_height()))
      item.draw()#draw the submenu if selectd
    else:
      screen.fill(unselBGColor,pygame.Rect(x,screenHeight-gooeyfont.get_linesize(),item.img.get_width(),item.img.get_height()))
    screen.blit(item.img,(x,screenHeight-gooeyfont.get_linesize()))
    x+=item.img.get_width()+1
    i+=1
    
def getSelectedSubMenu():
  return mainMenu[menuSelection]
  
def setSelectedSubMenu(newindex):
  global menuSelection
  menuSelection=newindex
  if newindex>len(mainMenu)-1:
    menuSelection=0
  elif newindex<0:
    menuSelection=len(mainMenu)-1
    
# MENU FUNCTIONS -----------------------------------------------

#def executeChildActions(smenu): #this is to be given to the menu to 

def setBrightness(spinner):
  camera.brightness=spinner.index
def setExposure(spinner):
  camera.exposure_compensation=spinner.index
def setContrast(spinner):
  camera.contrast=spinner.index
def setExpMode(menu):
  camera.exposure_mode=menu.getSelectedItem().text
def setIso(menu):
  if menu.index==0:
    camera.iso=0#Deal with the first menu item being "Auto"
  else:
    camera.iso=int(menu.getSelectedItem().text)#Cast the text string to an int. Not a great way to do this but w/e
def setAWB(menu):#Set a predefined white balance mode
  #camera.awb_mode=camera.AWB_MODES[menu.index]
  camera.awb_mode=menu.getSelectedItem().text#This is bad, but DJ's car is broken and I'm in a hurry


# GLOBAL STUFF -------------------------------------------------
screenWidth     = 160     #used for GUI scaling
screenHeight    = 128
screenMode      =  3      # Current screen mode; default = viewfinder
screenModePrior = -1      # Prior screen mode (for detecting changes)
menuSelection   =  0      # Index of selected menu Item in mainMenu
sizeMode        =  0      # Image size; default = Large
scaled          = None    # pygame Surface w/last-loaded image
fontSize        =  10
fontColor       = pygame.Color(255,255,255,255)
selectedBGColor	= pygame.Color(127,127,127,255)
unselBGColor    = pygame.Color(0,0,0,255)


#THESE NEED TO BE TWEAKED FOR SCREEN SIZES.
sizeData = [ # Camera parameters for different size settings
 # Full res      Viewfinder  Crop window
 [(2592, 1944), (160, 128), (0.0   , 0.0   , 1.0   , 1.0   )], # Large
 [(1920, 1080), (160, 96), (0.1296, 0.2222, 0.7408, 0.5556)], # Med
 [(1440, 1080), (160, 128), (0.2222, 0.2222, 0.5556, 0.5556)]] # Small

# Init framebuffer/touchscreen environment variables
os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_FBDEV'      , '/dev/fb1')

# Buffers for viewfinder data
rgb = bytearray(160 * 128 * 3)
yuv = bytearray(160 * 128 * 3 / 2)

pygame.init()
pygame.mouse.set_visible(False)
pygame.font.init()
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)

# Init camera and set up default values
camera            = picamera.PiCamera()
#considered camera.rotation=90
atexit.register(camera.close)
camera.resolution = sizeData[sizeMode][1]
camera.crop       = (0.0, 0.0, 1.0, 1.0)


#Set up Font
gooeyfont = pygame.font.SysFont(pygame.font.get_fonts()[1],fontSize,False,False)

#Set up Main Menu
mainMenu=[ #TODO: Make menu selections update when settings are changed externally
  SubMenu("R"),
  SubMenu("Time",
    MenuItem("1s"),
    MenuItem("5s"),
    MenuItem("10s"),
    MenuItem("20s"),
    MenuItem("30s"),
    MenuItem("1m")
  ),
  SubMenu("ISO",
    MenuItem("Auto"),
    MenuItem("100"),
    MenuItem("200"),
    MenuItem("320"),
    MenuItem("400"),
    MenuItem("500"),
    MenuItem("640"),
    MenuItem("800")
  ).setChange(setIso),
  SubDictMenu("AWB",picamera.PiCamera.AWB_MODES).setChange(setAWB).setIndex(1),
  SubDictMenu("Mode",picamera.PiCamera.EXPOSURE_MODES).setChange(setExpMode).setIndex(1),
  SubSpinner("B=",0,100,camera.brightness).setChange(setBrightness),
  SubSpinner("C=",-100,100,0).setChange(setContrast),
  SubSpinner("EXP=",-25,25,0).setChange(setExposure)
]


#print mainMenu



# MAIN LOOP ---------------------------------------------------------
while(True):
  #Handle keyboard input
  events = pygame.event.get()
  for event in events:
    if event.type == pygame.KEYDOWN:
      if event.key == pygame.K_LEFT:
        setSelectedSubMenu(menuSelection-1)
        #menuSelection-=1;
      if event.key == pygame.K_RIGHT:
        setSelectedSubMenu(menuSelection+1)
        #menuSelection+=1
      if event.key == pygame.K_UP:
        getSelectedSubMenu().setIndex(getSelectedSubMenu().index-1)
      if event.key == pygame.K_DOWN:
        getSelectedSubMenu().setIndex(getSelectedSubMenu().index+1)
      #if event.key == pygame.K_ENTER:
      if event.key == pygame.K_x:
        exit()

  # Refresh display(Literally Stolen from adafruit)
  if screenMode >= 3: # Viewfinder or settings modes
    stream = io.BytesIO() # Capture into in-memory stream
    camera.capture(stream, use_video_port=True, format='raw')
    stream.seek(0)
    stream.readinto(yuv)  # stream -> YUV buffer
    stream.close()
    yuv2rgb.convert(yuv, rgb, sizeData[sizeMode][1][0],
      sizeData[sizeMode][1][1])
    img = pygame.image.frombuffer(rgb[0:
      (sizeData[sizeMode][1][0] * sizeData[sizeMode][1][1] * 3)],
      sizeData[sizeMode][1], 'RGB')
  elif screenMode < 2: # Playback mode or delete confirmation
    img = scaled       # Show last-loaded image
  else:                # 'No Photos' mode
    img = None         # You get nothing, good day sir

  if img is None or img.get_height() < 240: # Letterbox, clear background
    screen.fill(0)
  if img:
    screen.blit(img,
      ((160 - img.get_width() ) / 2,
       (128 - img.get_height()) / 2))

  
  drawMenu()
  pygame.display.update()

  screenModePrior = screenMode
