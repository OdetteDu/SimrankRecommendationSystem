import numpy as np
import cPickle
from sets import Set
import math

USER_MIN = 0
USER_MAX = 130872
BUSINESS_MIN = 130873
BUSINESS_MAX = 136892

miuRating = 0

buser = [0 for i in range(USER_MIN, USER_MAX + 1)]
bbusiness = [0 for i in range(BUSINESS_MIN, BUSINESS_MAX + 1)]

userRateBusinessMap = {}
businessRatedByUserMap = {}
ratingMap = {}

userSimMatrix = cPickle.load(open("userMtx_3.pkl"))

bIntToIndex = cPickle.load(open("bIntToIndex.pkl"))
uIntToIndex = cPickle.load(open("uIntToIndex.pkl"))

print "Finished loadin user matrix pkl"

def arrayIndexToNodeIndex(currIndex, minIndex):
        return currIndex + minIndex

def nodeIndexToArrayIndex(currIndex, minIndex):
        return currIndex - minIndex

def init():
        sumRating = 0
        count = 0
        cuser = [0 for i in range(USER_MIN, USER_MAX + 1)]
        cbusiness = [0 for i in range(BUSINESS_MIN, BUSINESS_MAX + 1)]
        f = open("all_training.csv", "r")
        for line in f:
                temp = line.split(',', 2)
                user = int(temp[0])
                business = int(temp[1])
                rating = int(temp[2])
                # miu
                sumRating += rating
                count += 1
                # user average
                buser[nodeIndexToArrayIndex(user, USER_MIN)] += rating
                cuser[nodeIndexToArrayIndex(user, USER_MIN)] += 1
                # business average
                bbusiness[nodeIndexToArrayIndex(business, BUSINESS_MIN)] += rating
                cbusiness[nodeIndexToArrayIndex(business, BUSINESS_MIN)] += 1
                # user rate which business map
                if user in userRateBusinessMap:
                        userRateBusinessMap[user].add(business)
                else:
                        userRateBusinessMap[user] = Set([business])
                # business rated by which user map
                if business in businessRatedByUserMap:
                        businessRatedByUserMap[business].add(user)
                else:
                        businessRatedByUserMap[business] = Set([user])
                # user rating map
                ratingMap[(user, business)] = rating
        # Global avg
        global miuRating
        miuRating = sumRating * 1.0 / count
        # User avg
        for i in range(len(buser)):
                if cuser[i] != 0:
                        buser[i] = buser[i] * 1.0 / cuser[i]
        # Business avg
        for i in range(len(bbusiness)):
                if cbusiness[i] != 0:
                        bbusiness[i] = bbusiness[i] * 1.0 / cbusiness[i]
        print "Finish Init"

def calculateBaseline(user, business):
        return miuRating + (buser[nodeIndexToArrayIndex(user, USER_MIN)] - miuRating) + (bbusiness[nodeIndexToArrayIndex(business, BUSINESS_MIN)] - miuRating)

def getSimRankSimilarity(user1, user2):
        if user1 in uIntToIndex and user2 in uIntToIndex:
                return userSimMatrix[uIntToIndex[user1], uIntToIndex[user2]]*100
        else:
                return 0
        #return np.random.random()

def getCFSimilarity(user1, user2):
        if not (user1 in userRateBusinessMap and user2 in userRateBusinessMap):
                return 0
        businesses = userRateBusinessMap[user1].intersection(userRateBusinessMap[user2]) # businesses rated by both users
        if len(businesses)==0:
                return 0
        sum1 = 0
        sum2 = 0
        sum3 = 0
        for business in businesses:
                deviation1 = getRating(user1, business) - buser[nodeIndexToArrayIndex(user1, USER_MIN)]
                deviation2 = getRating(user2, business) - buser[nodeIndexToArrayIndex(user2, USER_MIN)]
                sum1 += deviation1 * deviation2
                sum2 += deviation1 * deviation1
                sum3 += deviation2 * deviation2
        if sum2 ==0 or sum3 ==0:
                return 0
        similarity = sum1 * 1.0 / (math.sqrt(sum2 * sum3 * 1.0))
        similarity = 1.0 / (1.0 + math.exp(-1.0 * similarity))
        return similarity

def getRating(user, business):
        return ratingMap[(user, business)]

def getMostSimilarUsers(user, business, maxNumUsers, method):
        if business in businessRatedByUserMap:
                userRatedBusiness = businessRatedByUserMap[business]
        else:
                userRatedBusiness = []
        userBusinessSimilarities = []
        for u in userRatedBusiness:
                if method == "SimRank":
                        userBusinessSimilarities.append((getSimRankSimilarity(user, u), u))
                if method == "CF":
                        userBusinessSimilarities.append((getCFSimilarity(user, u), u))
                if method == "random":
                        userBusinessSimilarities.append((np.random.random(), u))
        userBusinessSimilarities = sorted(userBusinessSimilarities, key = lambda x : -x[0])
        return userBusinessSimilarities[0 : min(maxNumUsers, len(userRatedBusiness))]

def estimateRating(user, business, method):
        maxNumUsers = 3
        userBusinessSimilarities = getMostSimilarUsers(user, business, maxNumUsers, method)
        weightedSum = 0
        simiaritySum = 0
        for ub in userBusinessSimilarities:
                weightedSum += ub[0] * (getRating(ub[1], business) * 1.0 - calculateBaseline(ub[1], business))
                simiaritySum += ub[0]
        if simiaritySum != 0:
                adjustScore = weightedSum * 1.0 / simiaritySum
        else:
                adjustScore = 0
        return calculateBaseline(user, business) + adjustScore

init()
f = open("all_test.csv", "r")
testCount = 0
simRankDeviation = 0
CFDeviation = 0
randomDeviation = 0
for line in f:
        testCount += 1
        temp = line.split(',', 2)
        user = int(temp[0])
        business = int(temp[1])
        rating = int(temp[2])
        if user in uIntToIndex and business in bIntToIndex:
                testCount += 1
                simRankDeviation += abs(rating - estimateRating(user, business, "SimRank"))
                CFDeviation += abs(rating - estimateRating(user, business, "CF"))
                randomDeviation += abs(rating - estimateRating(user, business, "random"))
                
print "Random average deviation is ", randomDeviation * 1.0 / testCount
print "SimRank average deviation is ", simRankDeviation * 1.0 / testCount
print "CF average deviation is ", CFDeviation * 1.0 / testCount
