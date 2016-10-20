from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal
from direct.directnotify.DirectNotifyGlobal import directNotify
from otp.distributed import OtpDoGlobals
from otp.otpbase import OTPLocalizer
from otp.otpbase import OTPGlobals
from otp.avatar.AvatarHandle import AvatarHandle
GUILDRANK_VETERAN = 4
GUILDRANK_GM = 3
GUILDRANK_OFFICER = 2
GUILDRANK_MEMBER = 1
import Queue

class GuildMemberInfo(AvatarHandle):

    def __init__(self, name, isOnline, rank, bandId):
        self.name = name
        self.rank = rank
        self.bandId = bandId
        self.onlineYesNo = isOnline

    def getName(self):
        return self.name

    def getRank(self):
        return self.rank

    def getBandId(self):
        return self.bandId

    def isOnline(self):
        return self.onlineYesNo

    def isUnderstandable(self):
        return True

    @report(types=['deltaStamp', 'args'], dConfigParam='teleport')
    def sendTeleportQuery(self, sendToId, localBandMgrId, localBandId, localGuildId, localShardId):
        base.cr.guildManager.d_reflectTeleportQuery(sendToId, localBandMgrId, localBandId, localGuildId, localShardId)

    @report(types=['deltaStamp', 'args'], dConfigParam='teleport')
    def sendTeleportResponse(self, available, shardId, instanceDoId, areaDoId, sendToId = None):
        base.cr.guildManager.d_reflectTeleportResponse(available, shardId, instanceDoId, areaDoId, sendToId)


class GuildManager(DistributedObjectGlobal):
    notify = directNotify.newCategory('GuildManager')

    def __init__(self, cr):
        DistributedObjectGlobal.__init__(self, cr)
        self.id2Name = {}
        self.id2BandId = {}
        self.id2Rank = {}
        self.id2Online = {}
        self.pendingMsgs = []

    def memberList(self):
        self.sendUpdate('requestMembers', [])

    def createGuild(self):
        messenger.send('declineGuildInvitation')
        self.sendUpdate('createGuild', [])

    def setWantName(self, newName):
        self.sendUpdate('setWantName', [newName])

    def removeMember(self, avatarId):
        self.sendUpdate('removeMember', [avatarId])

    def changeRank(self, avatarId, rank):
        self.sendUpdate('changeRank', [avatarId, rank])

    def changeRankAvocate(self, avatarId):
        self.sendUpdate('changeRankAvocate', [avatarId])

    def requestLeaderboardTopTen(self):
        self.sendUpdate('requestLeaderboardTopTen', [])

    def sendRequestInvite(self, avatarId):
        self.sendUpdate('requestInvite', [avatarId])

    def sendAcceptInvite(self):
        self.sendUpdate('acceptInvite', [])

    def sendDeclineInvite(self):
        self.sendUpdate('declineInvite', [])

    def sendTalk(self, msgText, chatFlags = 0):
        self.sendUpdate('sendChat', [msgText])

    def sendSC(self, msgIndex):
        self.sendUpdate('sendSC', [msgIndex])

    def sendSCQuest(self, questInt, msgType, taskNum):
        self.sendUpdate('sendSCQuest', [questInt, msgType, taskNum])

    def sendTokenRequest(self):
        self.sendUpdate('sendTokenRequest', [])

    def sendTokenForJoinRequest(self, token):
        name = base.localAvatar.getName()
        self.sendUpdate('sendTokenForJoinRequest', [token, name])

    def isInGuild(self, avId):
        return avId in self.id2Name

    def getRank(self, avId):
        return self.id2Rank.get(avId)

    def getBandId(self, avId):
        return self.id2BandId.get(avId)

    def getMemberInfo(self, avId):
        if self.isInGuild(avId):
            return GuildMemberInfo(self.id2Name[avId], self.id2Online[avId], self.id2Rank[avId], self.id2BandId[avId])
        return None

    def getOptionsFor(self, avId):
        if self.isInGuild(avId):
            myRank = self.id2Rank.get(localAvatar.doId, localAvatar.getGuildRank())
            hisRank = self.id2Rank[avId]
            canpromote = False
            candemote = False
            cankick = False
            if myRank == GUILDRANK_GM:
                canpromote = True
                candemote = True
                cankick = True
            if myRank > GUILDRANK_MEMBER and myRank != GUILDRANK_VETERAN and (hisRank <= GUILDRANK_MEMBER or hisRank == GUILDRANK_VETERAN):
                cankick = True
            return (canpromote, candemote, cankick)
        else:
            return None
        return None

    def updateTokenRValue(self, tokenString, rValue):
        rValue = int(rValue)
        self.sendUpdate('sendTokenRValue', [tokenString, rValue])
        if rValue == -1:
            base.localAvatar.guiMgr.guildPage.receivePermTokenValue(tokenString)

    def requestPermToken(self):
        self.sendUpdate('sendPermToken', [])

    def requestNonPermTokenCount(self):
        self.sendUpdate('sendNonPermTokenCount', [])

    def requestClearTokens(self, type):
        self.sendUpdate('sendClearTokens', [type])

    def receiveMembers(self, members):
        self.newList = []
        self.id2Name = {}
        self.id2Rank = {}
        self.id2BandId = {}

        for guy in members:
            id, name, rank, isOnline, bandMgrId, bandId = guy
            self.id2Name[id] = name
            self.id2Rank[id] = rank
            self.id2Online[id] = isOnline
            self.id2BandId[id] = (bandMgrId, bandId)

        for id, msg in self.pendingMsgs:
            if not base.localAvatar.isIgnored(id):
                base.talkAssistant.receiveGuildMessage(id, self.id2Name.get(id, 'Unknown'), msg)

        if hasattr(base, 'localAvatar'):
            base.localAvatar.guiMgr.guildPage.receiveMembers(members)

        messenger.send('guildMemberUpdated', sentArgs=[localAvatar.doId])

    def clearMembers(self):
        self.receiveMembers([])

    def guildStatusUpdate(self, guildId, guildName, guildRank):
        if hasattr(base, 'localAvatar'):
            base.localAvatar.guildStatusUpdate(guildId, guildName, guildRank)
        self.memberList()

    def guildNameReject(self, guildId):
        if hasattr(base, 'localAvatar'):
            base.localAvatar.guildNameReject(guildId)

    def guildNameChange(self, guildName, changeStatus):
        if hasattr(base, 'localAvatar'):
            base.localAvatar.guildNameChange(guildName, changeStatus)

    def guildNameUpdate(self, avatarId, guildName):
        print 'DEBUG - guildNameUpdate for ', avatarId, ' to ', guildName

    def invitationFrom(self, avatarId, avatarName, guildId, guildName):
        if hasattr(base, 'localAvatar'):
            base.localAvatar.guiMgr.handleGuildInvitation(avatarId, avatarName, guildId, guildName)

    def guildAcceptInvite(self):
        messenger.send(OTPGlobals.GuildAcceptInviteEvent)

    def leaderboardTopTen(self, stuff):
        base.localAvatar.guiMgr.handleTopTen(stuff)

    def guildRejectInvite(self, reason):
        messenger.send(OTPGlobals.GuildRejectInviteEvent, [reason])

    def rejectInvite(self, avatarId, reason):
        pass

    def recvChat(self, senderId, senderName, chat, garble=True):
        if not base.localAvatar.isIgnored(senderId):
            if base.whiteList and garble:
                chat = base.whiteList.processThroughAll(chat, base.chatGarbler)

            base.talkAssistant.receiveGuildTalk(senderId, senderName, chat)
    
    def recvSC(self, senderId, senderName, msgIndex):
        self.recvChat(senderId, senderName, OTPLocalizer.SpeedChatStaticText[msgIndex], False)

    def recvSCQuest(self, senderId, senderName, questInt, msgType, taskNum):
        message = base.talkAssistant.SCDecoder.decodeSCQuestMsgInt(questInt, msgType, taskNum)
        self.recvChat(senderId, senderName, message, False)

    def recvAvatarOnline(self, avatarId, avatarName):
        self.id2Online[avatarId] = True

        if hasattr(base, 'localAvatar') and avatarId != base.localAvatar.doId:
            if not base.localAvatar.isIgnored(avatarId):
                base.talkAssistant.receiveGuildUpdate(avatarId, avatarName, True)
            
            messenger.send('guildMemberOnlineStatus', [avatarId, 1])

    def recvAvatarOffline(self, avatarId, avatarName):
        self.id2BandId[avatarId] = (0, 0)
        self.id2Online[avatarId] = False

        if hasattr(base, 'localAvatar') and avatarId != base.localAvatar.doId:
            if not base.localAvatar.isIgnored(avatarId):
                base.talkAssistant.receiveGuildUpdate(avatarId, avatarName, False)
            
            messenger.send('guildMemberOnlineStatus', [avatarId, 0])

    def recvMemberAdded(self, memberInfo, inviterId, inviterName):
        avatarId, avatarName, rank, isOnline, bandManagerId, bandId = memberInfo
        self.id2Name[avatarId] = avatarName
        self.id2Rank[avatarId] = rank
        self.id2BandId[avatarId] = (bandManagerId, bandId)
        self.id2Online[avatarId] = isOnline
        if hasattr(base, 'localAvatar'):
            base.localAvatar.guiMgr.guildPage.addMember(memberInfo)
        messenger.send('guildMemberUpdated', sentArgs=[avatarId])

    def recvMemberRemoved(self, avatarId, senderId, avatarName, senderName):
        if avatarId == localAvatar.doId:
            self.clearMembers()
        else:
            self.id2Name.pop(avatarId, None)
            self.id2Rank.pop(avatarId, None)
            self.id2BandId.pop(avatarId, None)
            self.id2Online.pop(avatarId, None)
            if hasattr(base, 'localAvatar'):
                base.localAvatar.guiMgr.guildPage.removeMember(avatarId)
        messenger.send('guildMemberUpdated', sentArgs=[avatarId])
        return

    def recvMemberUpdateRank(self, avatarId, senderId, avatarName, senderName, rank, promote):
        self.id2Rank[avatarId] = rank
        if hasattr(base, 'localAvatar') and base.localAvatar.guiMgr:
            base.localAvatar.guiMgr.guildPage.updateGuildMemberRank(avatarId, rank)
        messenger.send('guildMemberUpdated', sentArgs=[avatarId])

    def recvMemberUpdateBandId(self, avatarId, bandManagerId, bandId):
        self.id2BandId[avatarId] = (bandManagerId, bandId)
        messenger.send('guildMemberUpdated', sentArgs=[avatarId])

    def recvTokenInviteValue(self, tokenValue, preExistPerm):
        if hasattr(base, 'localAvatar') and base.localAvatar.guiMgr:
            base.localAvatar.guiMgr.guildPage.displayInviteGuild(tokenValue, preExistPerm)

    def recvTokenRedeemMessage(self, guildName):
        if hasattr(base, 'localAvatar') and base.localAvatar.guiMgr:
            if guildName == '***ERROR - GUILD CODE INVALID***':
                base.localAvatar.guiMgr.guildPage.displayRedeemErrorMessage(OTPLocalizer.GuildRedeemErrorInvalidToken)
            elif guildName == '***ERROR - GUILD FULL***':
                base.localAvatar.guiMgr.guildPage.displayRedeemErrorMessage(OTPLocalizer.GuildRedeemErrorGuildFull)
            else:
                base.localAvatar.guiMgr.guildPage.displayRedeemConfirmMessage(guildName)

    def recvTokenRedeemedByPlayerMessage(self, redeemerName):
        if hasattr(base, 'localAvatar') and base.localAvatar.guiMgr:
            base.localAvatar.guiMgr.guildPage.notifyTokenGeneratorOfRedeem(redeemerName)

    def recvPermToken(self, token):
        if hasattr(base, 'localAvatar') and base.localAvatar.guiMgr:
            if token == '0':
                base.localAvatar.guiMgr.guildPage.receivePermTokenValue(None)
            else:
                base.localAvatar.guiMgr.guildPage.receivePermTokenValue(token)
        return

    def recvNonPermTokenCount(self, tCount):
        if hasattr(base, 'localAvatar') and base.localAvatar.guiMgr:
            base.localAvatar.guiMgr.guildPage.receiveNonPermTokenCount(tCount)

    @report(types=['deltaStamp', 'args'], dConfigParam='teleport')
    def d_reflectTeleportQuery(self, sendToId, localBandMgrId, localBandId, localGuildId, localShardId):
        self.sendUpdate('reflectTeleportQuery', [sendToId,
         localBandMgrId,
         localBandId,
         localGuildId,
         localShardId])

    @report(types=['deltaStamp', 'args'], dConfigParam='teleport')
    def teleportQuery(self, requesterId, requesterBandMgrId, requesterBandId, requesterGuildId, requesterShardId):
        if self.cr.teleportMgr:
            self.cr.teleportMgr.handleAvatarTeleportQuery(requesterId, requesterBandMgrId, requesterBandId, requesterGuildId, requesterShardId)

    @report(types=['deltaStamp', 'args'], dConfigParam='teleport')
    def d_reflectTeleportResponse(self, available, shardId, instanceDoId, areaDoId, sendToId):
        self.sendUpdate('reflectTeleportResponse', [sendToId,
         available,
         shardId,
         instanceDoId,
         areaDoId])

    @report(types=['deltaStamp', 'args'], dConfigParam='teleport')
    def teleportResponse(self, responderId, available, shardId, instanceDoId, areaDoId):
        if self.cr.teleportMgr:
            self.cr.teleportMgr.handleAvatarTeleportResponse(responderId, available, shardId, instanceDoId, areaDoId)
