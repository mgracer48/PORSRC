from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.distributed.ClockDelta import globalClockDelta
from direct.directnotify import DirectNotifyGlobal
from direct.task import Task
from TimeOfDayManagerBase import TimeOfDayManagerBase
from pirates.piratesbase import TODGlobals
from direct.distributed.ClockDelta import globalClockDelta
from otp.ai.MagicWordGlobal import *
import TODGlobals
import time
import random


class DistributedTimeOfDayManagerAI(DistributedObjectAI, TimeOfDayManagerBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTimeOfDayManagerAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        TimeOfDayManagerBase.__init__(self)
        self.isPaused = False
        self.cycleType = TODGlobals.TOD_REGULAR_CYCLE
        self.cycleSpeed = 1
        self.tempTime = globalClockDelta.getFrameNetworkTime(bits = 32)
        self.startingNetTime = globalClockDelta.networkToLocalTime(self.tempTime)
        self.timeOffset = 0
        self.envSubEntry = []
        self.isJolly = 0
        self.isRain = 0
        self.isStorm = 0
        self.isDarkFog = 0
        self.clouds = TODGlobals.LIGHTCLOUDS
        self.weather = (TODGlobals.WEATHER_CLEAR, 0)
        self.fromCurrent = 0
        self.startPhase = 0
        self.targetPhase = 0
        self.targetTime = 0

    def announceGenerate(self):
        DistributedObjectAI.announceGenerate(self)
        if config.GetBool('advanced-weather', False):
            self.__runWeather()
            self.runWeather = taskMgr.doMethodLater(15, self.__runWeather, 'runWeather')

    def delete(self):
        DistributedObjectAI.delete(self)
        if hasattr(self, 'runWeather'):
            taskMgr.remove(self.runWeather)

    def setWeather(self, type=0, time=0):
        weather, otime = self.weather
        self.weather = (type, time)
        
        if type != weather:
            self.notify.debug("Changing weather state to %s" % type)
            weatherInfo = TODGlobals.WEATHER_ENVIROMENTS[type]
            if not weatherInfo:
                self.notify.warning("Failed to update weather state. %s is not a valid weather enviroment" % type)
                return
            self.setRain(weatherInfo['rain'])
            self.setStorm(weatherInfo['storm'])
            self.setBlackFog(weatherInfo['darkfog'])
            self.setClouds(weatherInfo['sky'])

    def pickWeather(self):
        dice = random.random()
        
        if dice <= 50:
            return TODGlobals.WEATHER_CLEAR
        elif config.GetBool('want-storm-weather', False) and dice <= 75:
            return TODGlobals.WEATHER_STORM

        return TODGlobals.WEATHER_RAIN

    def __runWeather(self, task=None):
        if self.isPaused:
            return Task.again

        type, time = self.weather
        time -= 15

        if not task:
            type = TODGlobals.WEATHER_CLEAR
            time = 1200
        elif time <= 0:
            type, time = self.pickWeather()
 
        self.setWeather(type, time)
        return Task.again

    def syncTOD(self, cycleType, cycleSpeed, startingNetTime, timeOffset):
        self.cycleType = cycleType
        self.cycleSpeed = cycleSpeed
        self.startingNetTime = startingNetTime
        self.timeOffset = timeOffset

    def getSyncTOD(self):
        return (self.cycleType, self.cycleSpeed, self.startingNetTime, self.timeOffset)

    def setIsPaused(self, isPaused):
        self.isPaused = isPaused
        self.sendUpdate('setIsPaused', [isPaused])

    def getIsPaused(self):
        return self.isPaused

    def requestSync(self):
        pass #TODO

    def setEnvSubs(self, envSubEntry):
        self.envSubEntry = envSubEntry

    def getEnvSubs(self):
        return self.envSubEntry

    def setMoonPhaseChange(self, fromCurrent, startPhase, targetPhase, targetTime):
        self.fromCurrent = fromCurrent
        self.startPhase = startPhase
        self.targetPhase = targetPhase
        self.targetTime = targetTime

    def getMoonPhaseChange(self):
        return (self.fromCurrent, self.startPhase, self.targetPhase, self.targetTime)

    def setMoonJolly(self, isJolly):
        self.isJolly = isJolly
        self.sendUpdate('setMoonJolly', [isJolly])

    def getMoonJolly(self):
        return self.isJolly

    def setRain(self, isRain):
        self.isRain = isRain
        self.sendUpdate('setRain', [isRain])

    def getRain(self):
        return self.isRain

    def setStorm(self, isStorm):
        self.isStorm = isStorm
        self.sendUpdate('setStorm', [isStorm])

    def getStorm(self):
        return self.isStorm

    def setBlackFog(self, isDarkFog):
        self.isDarkFog = isDarkFog
        self.sendUpdate('setBlackFog', [isDarkFog])

    def getBlackFog(self):
        return self.isDarkFog

    def setClouds(self, cloudType):
        self.clouds = cloudType
        self.sendUpdate('setClouds', [cloudType])

    def getClouds(self):
        return self.clouds

@magicWord(CATEGORY_GAME_MASTER, types=[int, int])
def setWeather(weatherId, time=0):
    if config.GetBool('advanced-weather', False):

        if weatherId not in TODGlobals.WEATHER_ENVIROMENTS:
            available = TODGlobals.WEATHER_ENVIROMENTS.keys()
            return "%s is an invalid weather id. Available keys are %s " % (weatherId, available)

        simbase.air.todManager.setWeather(weatherId, time)
        return "Setting weather state to %s for the district for a duration of %s." % (weatherId, time)
    return "Sorry, Weather is not enabled on this district."

@magicWord(CATEGORY_GAME_MASTER)
def getWeather():
    weather, time = simbase.air.todManager.weather
    return "Current district weather is set to %s for a duration of %s" % (weather, time)

@magicWord(CATEGORY_GAME_MASTER)
def weatherReady():
    return "Weather Ready: %s" % str(config.GetBool('advanced-weather', False))


@magicWord(CATEGORY_GAME_MASTER, types=[int])
def setRain(state):
    if config.GetBool('advanced-weather', False):
        simbase.air.todManager.setRain((state == 1))
        return 'Setting rain state to %s for district.' % state
    return "Sorry, Weather is not enabled on this district."

@magicWord(CATEGORY_GAME_MASTER, types=[int])
def setStorm(state):
    if config.GetBool('advanced-weather', False):
        if config.GetBool('want-storm-weather', False):
            simbase.air.todManager.setStorm((state == 1))
            return 'Setting storm state to %s for district.' % state
        else:
            return "Sorry, Storms are not enabled on this district."
    return "Sorry, Weather is not enabled on this district."

@magicWord(CATEGORY_GAME_MASTER, types=[int])
def setDarkFog(state):
    if config.GetBool('advanced-weather', False):
        simbase.air.todManager.setBlackFog((state == 1))
        return 'Setting dark fog state to %s for district.' % state
    return "Sorry, Weather is not enabled on this district."

@magicWord(CATEGORY_GAME_MASTER, types=[int])
def setClouds(state):
    if config.GetBool('advanced-weather', False):
        simbase.air.todManager.setClouds(state)
        return 'Setting cloud state to %s for district.' % state
    return "Sorry, Weather is not enabled on this district."

@magicWord(CATEGORY_GAME_MASTER, types=[int])
def setJollyMoon(state):
    simbase.air.todManager.setMoonJolly((state == 1))
    return "Setting jolly moon state to %s for district." % state