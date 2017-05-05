from otp.distributed.DistributedDistrictAI import DistributedDistrictAI
from pirates.piratesbase import PiratesGlobals
from pirates.world import WorldGlobals

import time

class PiratesDistrictAI(DistributedDistrictAI):
    parentingRules = ('', '')
    mainWorld = WorldGlobals.PiratesWorldSceneFileBase
    tutorialWorld = WorldGlobals.PiratesTutorialSceneFileBase
    shardType = PiratesGlobals.SHARD_MAIN

    def announceGenerate(self):
        DistributedDistrictAI.announceGenerate(self)

        self.created = int(time.time())
        self.accept('queryShardStatus', self.d_updateRPCStatus)
        self.air.addPostRemove(self.air.prepareMessage('shardDeath'))

        self.d_updateRPCStatus()

    def d_updateRPCStatus(self):
        # Send a shard status update with the information we have:
        status = {
            'available': bool(self.available),
            'name': self.name,
            'created': self.created
        }
        self.air.sendNetEvent('shardStatus', [status])

    def setParentingRules(self, rule1, rule2):
        self.parentingRules = (rule1, rule2)

    def d_setParentingRules(self, rule1, rule2):
        self.sendUpdate('setParentingRules', [rule1, rule2])

    def b_setParentingRules(self, rule1, rule2):
        self.setParentingRules(rule1, rule2)
        self.d_setParentingRules(rule1, rule2)

    def getParentingRules(self):
        return self.parentingRules

    def setMainWorld(self, mainWorld):
        self.mainWorld = mainWorld

    def d_setMainWorld(self, mainWorld):
        self.sendUpdate('setMainWorld', [mainWorld])

    def b_setMainWorld(self, mainWorld):
        self.setMainWorld(mainWorld)
        self.d_setMainWorld(mainWorld)

    def getMainWorld(self):
        return self.mainWorld

    def setShardType(self, shardType):
        self.shardType = shardType

    def d_setShardType(self, shardType):
        self.sendUpdate('setShardType', [shardType])

    def b_setShardType(self, shardType):
        self.setShardType(shardType)
        self.b_setShardType(shardType)

    def getShardType(self):
        return self.shardType

    def d_setAvailable(self, available):
        DistributedDistrictAI.d_setAvailable(self, available)
        self.d_updateRPCStatus()

    def rpcSetAvailable(self, available):
        self.b_setAvailable(available)
