from panda3d.core import NodePath, getModelPath
from direct.distributed.DistributedNodeAI import DistributedNodeAI
from direct.distributed.GridParent import GridParent
from direct.task import Task
from pirates.battle.DistributedEnemySpawnerAI import DistributedEnemySpawnerAI
from pirates.interact.DistributedSearchableContainerAI import DistributedSearchableContainerAI
from pirates.interact.DistributedInteractivePropAI import DistributedInteractivePropAI
from pirates.minigame.DistributedPokerTableAI import DistributedPokerTableAI
from pirates.minigame.DistributedBlackjackTableAI import DistributedBlackjackTableAI
from pirates.minigame.DistributedHoldemTableAI import DistributedHoldemTableAI
from pirates.minigame.Distributed7StudTableAI import Distributed7StudTableAI
from pirates.minigame.DistributedLiarsDiceAI import DistributedLiarsDiceAI
from pirates.holiday.DistributedHolidayObjectAI import DistributedHolidayObjectAI
from pirates.holiday.DistributedHolidayPigAI import DistributedHolidayPigAI
from pirates.holiday.DistributedHolidayBonfireAI import DistributedHolidayBonfireAI
from pirates.quest.DistributedQuestPropAI import DistributedQuestPropAI
from pirates.world.DistributedFortAI import DistributedFortAI
from pirates.world import WorldGlobals
from pirates.ai import HolidayGlobals

class DistributedGameAreaAI(DistributedNodeAI):

    BossSpawnKeys = ['Skeleton', 'NavySailor', 'Creature']

    def __init__(self, air, modelPath):
        DistributedNodeAI.__init__(self, air)

        self.uid = ''
        self.name = ''
        self.modelPath = modelPath

        self.buildingInterior = False

        self.spawner = DistributedEnemySpawnerAI(self)
        self.npcs = {}

        self._movementNodes = {}
        self._movementPaths = {}

        self.wantNPCS = config.GetBool('want-npcs', False)
        self.wantEnemies = config.GetBool('want-enemies', False)
        self.wantBosses = config.GetBool('want-bosses', True)
        self.wantForts = config.GetBool('want-forts', True)
        self.wantQuestProps = config.GetBool('want-quest-props', True)

        self.wantHolidayObjects = config.GetBool('want-holiday-objects', True)
        self._holidayNPCs = {}

        self.debugPrints = config.GetBool('want-debug-world-prints', True)

        self.wantInvasions = config.GetBool('want-invasions', True)
        self._invasionSpawns = {}

        self.setPythonTag('npTag-gameArea', self)

    def announceGenerate(self):
        DistributedNodeAI.announceGenerate(self)
        self.accept('holidayListChanged', self.handleHolidayChange)

    def delete(self):
        DistributedNodeAI.delete(self)
        self.ignore('holidayListChanged')

    def setUniqueId(self, uid):
        self.uid = uid
        self.air.uid2do[uid] = self

    def d_setUniqueId(self, uid):
        self.sendUpdate('setUniqueId', [uid])

    def b_setUniqueId(self, uid):
        self.setUniqueId(uid)
        self.d_setUniqueId(uid)

    def getUniqueId(self):
        return self.uid

    def setName(self, name):
        self.name = name

    def d_setName(self, name):
        self.sendUpdate('setName', [name])

    def b_setName(self, name):
        self.setName(name)
        self.d_setName(name)

    def getName(self):
        return self.name

    def getModelPath(self):
        return self.modelPath

    def createObject(self, objType, parent, objKey, object):
        genObj = None

        if objType == 'Animal' and config.GetBool('want-animals', False):
            self.spawner.addAnimalSpawnNode(objKey, object)

        elif objType == 'Townsperson' and self.wantNPCS:
            genObj = self.generateNPC(objType, objKey, object)

        elif objType in self.BossSpawnKeys and self.wantBosses and self.wantEnemies:
            genObj = self.generateBoss(objType, objKey, object)

        elif objType == 'Spawn Node' and self.wantEnemies:
            self.spawner.addEnemySpawnNode(objType, objKey, object)

        elif objType == 'Dormant NPC Spawn Node' and self.wantEnemies and config.GetBool('want-dormant-spawns', False):
            self.spawner.addEnemySpawnNode(objType, objKey, object)

        elif objType == 'Movement Node' and self.wantEnemies:
            genObj = self.generateNode(objType, objKey, object, parent)
            self._movementNodes[objKey] = genObj

        elif objType == 'Searchable Container' and config.GetBool('want-searchables', False):
            genObj = DistributedSearchableContainerAI.makeFromObjectKey(self.air, objKey, object)
            self.generateChild(genObj)

        elif objType == 'Holiday' and self.wantHolidayObjects:
            #self.__printUnimplementedNotice(objType) #TODO
            genObj = self.generateNode(objType, objKey, object, parent, gridPos=True)

        elif objType == 'Holiday Object' and self.wantHolidayObjects:
            subType = object.get('SubType')
            if subType == 'Roast Pig':
                genObj = DistributedHolidayPigAI.makeFromObjectKey(self.air, objKey, object)
            elif subType == 'Bonfire':
                genObj = DistributedHolidayBonfireAI.makeFromObjectKey(self.air, objKey, object)
            else:
                self.notify.warning("Unsupported Holiday Object SubType: %s" % subType)

        elif objType == 'Building Exterior':
            genObj = self.air.worldCreator.createBuilding(self, objKey, object)

        elif objType == 'Island Game Area' and config.GetBool('want-link-tunnels', False):
            self.__printUnimplementedNotice(objType)

        elif objType == 'Invasion Barricade' and self.wantInvasions:
            genObj = self.generateNode(objType, objKey, object, parent, gridPos=True)

        elif objType == 'Invasion Barrier' and self.wantInvasions:
            genObj = self.generateNode(objType, objKey, object, parent, gridPos=True)

        elif objType == 'Invasion NPC Spawn Node' and self.wantInvasions:
            self._invasionSpawns[objKey] = self.generateNode(objType, objKey, object, parent, gridPos=True)
            if config.GetBool('force-invasion-spawns', True):
                self.spawner.addEnemySpawnNode(objType, objKey, object)

        elif objType == 'Fort' and self.wantForts: #TODO find objType
            self.notify.info("Spawning %s on %s" % (objType, self.getName()))
            genObj = DistributedFortAI.makeFromObjectKey(self.air, objKey, object)
            #self.__printUnimplementedNotice(objType)

        elif objType == 'Interactive Prop':
            #self.__printUnimplementedNotice(objType) #TODO object doesnt properly spawn
            genObj = DistributedInteractivePropAI.makeFromObjectKey(self.air, objKey, object)

        elif objType == 'Quest Prop' and self.wantQuestProps:
            self.__printUnimplementedNotice(objType) #TODO
            #DistributedQuestPropAI.makeFromObjectKey(self.air, objKey, object)

        elif objType == 'Parlor Game' and config.GetBool('want-parlor-games', True):
            gameType = object.get('Category', 'Poker')
            if gameType == "Blackjack":
                genObj = DistributedBlackjackTableAI.makeFromObjectKey(self.air, objKey, object)
            elif gameType == "Poker":
                genObj = DistributedPokerTableAI.makeFromObjectKey(self.air, objKey, object)
            elif gameType == "Holdem":
               genObj = DistributedHoldemTableAI.makeFromObjectKey(self.air, objKey, object)
            elif gameType == "7Stud":
                genObj = Distributed7StudTableAI.makeFromObjectKey(self.air, objKey, object)
            else:
                self.notify.warning("Unknown Parlor Game type: %s" % gameType)

            if genObj != None:
                self.generateChild(genObj, cellParent = True)

        elif objType == 'Dice Game' and config.GetBool('want-dice-games', True):
            gameType = object.get('Category', 'Dice')
            if gameType == "Liars":
                genObj = DistributedLiarsDiceAI.makeFromObjectKey(self.air, objKey, object)
            else:
                self.notify.warning("Unknown Dice Game type: %s" % gameType)

            if genObj != None:
                self.generateChild(genObj, cellParent = True)

        elif objType == 'Collision Barrier':
            genObj = self.generateNode(objType, objKey, object, parent)

        else:
            self.__logMissing(objType)
            genObj = self.generateNode(objType, objKey, object, parent, gridPos=True)

        return genObj

    def __printDebugInfo(self, objType, data):
        if self.debugPrints:
            self.notify.info("Type: %s Data: %s" % (objType, data))

    def __printUnimplementedNotice(self, objType):
        from pirates.world.WorldCreatorAI import WorldCreatorAI
        WorldCreatorAI.registerUnimplemented(objType)

    def __logMissing(self, objType):
        if not self.debugPrints:
            return

        ignoreList = [
            'Port Collision Sphere',
            'Ambient SFX Node',
            'Animated Avatar - Navy',
            'Player Spawn Node',
            'Shop - Jeweler',
            'Shop - Tailor',
            'Shop - Barber',
            'Furniture',
            'Hay',
            'Barrel',
            'Pig_stuff',
            'Location Sphere',
            'Horse_trough',
            'Crane',
            'Mortar_Pestle',
            'Cacti',
            'Spanish Walls',
            'Voodoo',
            'Volcano',
            'Log_Stack',
            'Grass',
            'Stairs',
            'Sack',
            'Cups',
            'Shanty Gypsywagon',
            'Shanty Tents',
            'Flower_Pots',
            'Pier',
            'Cemetary',
            'LaundryRope',
            'TreeBase',
            'Swamp_props',
            'Paddle',
            'Bush',
            'Fountain',
            'Swamp_props_small',
            'Tunnel Cap',
            'Burnt_Props',
            'Pan',
            'Military_props',
            'Interior_furnishings',
            'Jungle_Props',
            'Food',
            'Cart',
            'Pots',
            'Wall_Hangings',
            'Enemy_Props',
            'Arch',
            'Chimney',
            'Jugs_and_Jars',
            'Tree - Animated',
            'FountainSmall',
            'Shop - Fisherman',
            'Bucket',
            'Tree',
            'Vines',
            'Rope',
            'Prop_Groups',
            'Rock',
            'Trellis',
            'Light - Dynamic',
            'Ship_Props',
            'Bridge',
            'Cave_Props',
            'Well',
            'Cave_Pieces',
            'Writing_Paper',
            'Furniture - Fancy',
            'Wall',
            'Crate',
            'Baskets',
            'Ocean_Props',
            'Mining_props',
            'Tools',
            'Jungle_Props_large',
            'Treasure Chest',
            'Trunks',
            'Light_Fixtures',
            'ChickenCage',
            'Effect Node',
            'Player Boot Node',
            'Ship Wreck',
            'Quest Node',
            'Switch Prop',
            'Jail Cell Door',
            'Portal Node',
            'Simple Fort',
            'Locator Node',
            'Door Locator Node'
        ]

        configurables = {
            'want-npcs': [False, ['Townsperson']],
            'want-enemies': [False, ['Spawn Node', 'Dormant NPC Spawn Node']],
            'want-bosses': [False, self.BossSpawnKeys],
            'want-forts': [True, ['Fort']], #TODO find proper key
            'want-quest-props': [True, ['Quest Prop']],
            'want-link-tunnels': [False, ['Island Game Area', 'Connector Tunnel']],
            'want-searchables': [False, ['Searchable Container']],
            'want-animals': [False, ['Animal']],
            'want-parlor-games': [True, ['Parlor Game']],
            'want-dice-games': [True, ['Dice Game']],
            'want-holiday-objects': [True, ['Holiday', 'Holiday Object']],
            'want-invasions': [True, ['Invasion Barricade', 'Invasion Barrier', 'Invasion NPC Spawn Node']]
        }
        for configKey in configurables:
            configurableData = configurables[configKey]
            configDefault = configurableData[0]
            ignores = configurableData[1]
            if not config.GetBool(configKey, configDefault) and len(ignores) > 0:
                for item in ignores:
                    if item not in ignoreList:
                        ignoreList.append(item)

        if objType in ignoreList and config.GetBool('want-debug-ignore-list', True):
            return

        from pirates.world.WorldCreatorAI import WorldCreatorAI
        WorldCreatorAI.registerMissing(objType)

    def handleHolidayChange(self):
        if not self.air.newsManager:
            return
        holidayList = self.air.newsManager.getRawHolidayIdList()
        self.__processHolidayNPCs(holidayList)

    def __processHolidayNPCs(self, holidayIdList):
        if len(self._holidayNPCs) <= 0:
            return

        for objKey in self._holidayNPCs:
            npcData = self._holidayNPCs[objKey]
            objType = npcData[0]
            object = npcData[1]
            currentNPC = npcData[2]
            holidayId = HolidayGlobals.getHolidayIdFromName(object.get('Holiday', ''))
            self.notify.debug("holidayId: %s currentNPC: %s" % (holidayId, str(currentNPC)))
            if holidayId in holidayIdList and currentNPC is None:
                genNPC = self.generateNPC(objType, objKey, object, forceHoliday=True)
                self._holidayNPCs[objKey][2] = genNPC
            else:
                if currentNPC is not None:
                    currentNPC.delete()
                    self._holidayNPCs[objKey][2] = None

    def generateNPC(self, objType, objKey, object, forceHoliday=False):
        genObj = None
        boss = object.get('Boss', False)
        if not boss:
            holiday = object.get('Holiday', '')
            alwaysShow = config.GetBool('always-show-holiday-npcs', False)
            holidayRunning = False

            if holiday != '' and not forceHoliday:
                holidayId = HolidayGlobals.getHolidayIdFromName(holiday)
                holidayRunning = self.air.newsManager.isHolidayRunning(holidayId)
                if not alwaysShow: 
                    self.notify.info("Storing Holiday(%s) NPC: %s " % (holiday, objKey))
                    self._holidayNPCs[objKey] = [objType, object, None]

            if holiday == '' or holidayRunning or alwaysShow or forceHoliday:

                genObj = self.spawner.spawnNPC(objKey, object)
                self.npcs[genObj.doId] = genObj

                gridPos = object.get('GridPos')
                if gridPos and isinstance(parent, NodePath):
                    genObj.setPos(self, gridPos)
                    genObj.d_updateSmPos()
                    newZoneId = self.getZoneFromXYZ(genObj.getPos(self))
                    genObj.b_setLocation(genObj.parentId, newZoneId)
        else:
            if self.wantBosses:
                self.notify.warning("Unable to spawn %s. Boss not yet supported" % objType)
                self.generateBoss(objType, objKey, object)
        return genObj

    def generateBoss(self, objType, objKey, object):
        genObj = None
        self.notify.info("Spawning Boss on %s with type %s" % (self.getName(), objType))
        if objType == 'Skeleton':
            self.__printUnimplementedNotice(objType) #TODO
            #self.spawner.addEnemySpawnNode(objType, objKey, object)
        elif objType == 'NavySailor':
            self.__printUnimplementedNotice(objType) #TODO
        elif objType == 'Creature':
            #self.__printUnimplementedNotice(objType) #TODO
            self.spawner.addEnemySpawnNode(objType, objKey, object)
        elif objType == 'Ghost':
            self.__printUnimplementedNotice(objType) #TODO
        elif objType == 'Townsperson':
            self.__printUnimplementedNotice(objType) #TODO
        else:
            self.__printUnimplementedNotice(objType)
        return genObj

    def generateChild(self, obj, zoneId=None, cellParent=False):

        if not hasattr(obj, 'getPos') and zoneId is None:
            self.notify.warning("Failed to spawn %s. Object does not have a getPos()" % type(obj).__name__)
            return

        if zoneId is None:
            zoneId = self.getZoneFromXYZ(obj.getPos())

        obj.generateWithRequiredAndId(self.air.allocateChannel(), self.doId, zoneId)

        if hasattr(obj, 'posControlledByCell'):
            cellParent = obj.posControlledByCell()

        if hasattr(obj, 'posControlledByIsland'): #LEGACY.
            self.notify.warning("posControlledByIsland is deprecated. Please switch '%s' to posControlledByCell as soon as possible." % type(obj).__name__)
            cellParent = obj.posControlledByIsland()

        if cellParent: 
            cell = GridParent.getCellOrigin(self, zoneId)
            pos = obj.getPos()

            obj.reparentTo(cell)
            obj.setPos(self, pos)

            obj.sendUpdate('setPos', obj.getPos())
            obj.sendUpdate('setHpr', obj.getHpr())

    def generateNode(self, objType, objKey, object, parent=None, gridPos=False, noLight=False):
        genObj = None
        nodeName =  'objNode-%s-%s' % (objType, objKey)

        if isinstance(parent, NodePath):
            genObj = parent.attachNewNode(nodeName)
        else:
            genObj = NodePath(nodeName)

        if 'Pos' in object:
            genObj.setPos(object['Pos'])

        if 'Hpr' in object:
            genObj.setHpr(object['Hpr'])

        if 'Scale' in object:
            genObj.setScale(object['Scale'])

        if 'GridPos' in object and gridPos:
            genObj.setPos(object['GridPos'])

        if noLight:
            genObj.setLightOff()

        return genObj