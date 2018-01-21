import ply.lex as lex
import re

# token names
tokens = (
    'PREDICATE',
    'VARIABLE',
    'OR',
    'NOT',
    'LPAREN',
    'RPAREN',
    'CONSTANT'
)

# regex for tokens lex
t_OR = r'\|'
t_NOT = r'\~'
t_VARIABLE = r'[a-z0-9]+'
t_PREDICATE = r'[A-Za-z]+\(.*?\)'
t_LPAREN = r'\( '
t_RPAREN = r' \)'
t_CONSTANT = r'\w+'


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


# A string containing ignored characters (spaces and tabs)
t_ignore = ' \t'


def t_error(t):
    t.lexer.skip(1)


# Build the lexer
lexer = lex.lex()

predicate_dict = {}
variable_dict = {}
constant_dict = {}

kb_Dict = {}


def parseSentence(inputSentence, lineNo):
    parsedTokens = []
    lexer.input(inputSentence)
    negationPresent = False
    while True:
        token = lexer.token()
        if not token:
            break
        parsedTokens.append((token.type, token.value, lineNo, token.lexpos))
        if token.type == 'NOT':
            negationPresent = True
        elif token.type == 'PREDICATE':
            if negationPresent:
                token.value = "~" + token.value
                negationPresent = False
            if token.value in predicate_dict:
                if lineNo not in predicate_dict[token.value]:
                    lineNoList = predicate_dict[token.value]
                    lineNoList.append(lineNo)
                    predicate_dict[token.value] = lineNoList
            else:
                predicate_dict[token.value] = [lineNo]

    for predicate in predicate_dict.keys():
        argsString = predicate[predicate.find('(') + 1:predicate.find(')')]
        args = argsString.split(',')
        for argument in args:
            lexer.input(argument)
            token = lexer.token()
            if token.type == 'VARIABLE':
                if token.value in variable_dict:
                    if token.lineno not in variable_dict[token.value]:
                        lineNoList = variable_dict[token.value]
                        lineNoList.append(predicate)
                        variable_dict[token.value] = lineNoList
                else:
                    variable_dict[token.value] = [predicate]
            elif token.type == 'CONSTANT':
                if token.value in constant_dict:
                    if token.lineno not in constant_dict[token.value]:
                        lineNoList = constant_dict[token.value]
                        lineNoList.append(predicate)
                        constant_dict[token.value] = lineNoList
                else:
                    constant_dict[token.value] = [predicate]
    return parsedTokens


def copyList(inputList):
    outputList = []
    for item in inputList:
        outputList.append(item)
    return outputList


def getPredicateName(predicate):
    return predicate.split("(")[0]


truePredicateDict = {}


def parseArgsInPred(args):
    parsedArgsList = []
    for argument in args:
        lexer.input(argument)
        token = lexer.token()
        parsedArgsList.append((token.type, token.value, token.lexpos))
    return parsedArgsList


def getArgsList(predicate):
    argsListWithComma = predicate[predicate.find('(') + 1: predicate.find(')')]
    return argsListWithComma.split(',')


def unify(predName, predArgs, unificationDic):
    unifiedArgs = []
    parsedPredArgs = parseArgsInPred(predArgs)
    keys = []
    for keyTuple in unificationDic.keys():
        keys.append(keyTuple[1])
    for (elementType, elementValue, elementPos) in parsedPredArgs:
        if elementValue in keys and elementType == 'VARIABLE':
            unifiedArgs.append((unificationDic[(elementType, elementValue)][1]))
        elif elementType == 'CONSTANT':
            unifiedArgs.append((elementValue))
        else:
            unifiedArgs.append(elementValue)
    unifiedPred = predName + "(" + ",".join(unifiedArgs) + ")"
    return unifiedPred


def unifyKbSentence(kbSentence, unificationDict):
    unifiedPredcates = []
    for predicate in kbSentence.split("|"):
        predicateArgs = getArgsList(predicate)
        keys = unificationDict.keys()
        elemValList = []
        for keyTuple in keys:
            elemValList.append(keyTuple[1])
        if set(elemValList) & set(predicateArgs):
            unifiedPredcates.append(unify(getPredicateName(predicate), predicateArgs, unificationDict))
        else:
            unifiedPredcates.append(predicate)
    return " | ".join(unifiedPredcates)


def negPredList(predicate, KB):
    negPredLineNoList = []
    if "~" in predicate:
        negatedPredicate = predicate.replace("~", "")
    else:
        negatedPredicate = "~" + predicate
    predicateNameToSearch = getPredicateName(negatedPredicate)
    for key in KB.keys():
        kbSentence = KB[key]
        kbSentencePreds = kbSentence.split("|")
        predicateNamesList = []
        for predicate in kbSentencePreds:
            predicateNamesList.append(getPredicateName(predicate.replace(" ", "")))
        if predicateNameToSearch in predicateNamesList:
            negPredLineNoList.append(key)
    return negPredLineNoList


def isUnificationAllowed(pred1, pred2):
    pred1Args = getArgsList(pred1)
    pred2Args = getArgsList(pred2)
    pred1parsedArgs = parseArgsInPred(pred1Args)
    pred2parsedArgs = parseArgsInPred(pred2Args)
    for i in range(len(pred2Args)):
        (elementType, elementValue, elementPos) = pred1parsedArgs[i]
        (elementType2, elementValue2, elementPos2) = pred2parsedArgs[i]
        if elementType == 'CONSTANT' and elementType2 == 'CONSTANT' and elementValue != elementValue2:
            return False
    return True


def predicateMatching(pred1, pred2):
    predArgsDict = {}
    pred1ArgsList = getArgsList(pred1)
    pred2ArgsList = getArgsList(pred2)
    pred1parsedArgs = parseArgsInPred(pred1ArgsList)
    pred2parsedArgs = parseArgsInPred(pred2ArgsList)

    for i in range(len(pred2ArgsList)):
        (arg1Type, arg1Val, arg1Pos) = pred1parsedArgs[i]
        (arg2Type, arg2Val, arg2Pos) = pred2parsedArgs[i]
        if arg1Type == 'CONSTANT' and arg2Type == 'VARIABLE':
            if (arg2Type, arg2Val) in predArgsDict.keys() and predArgsDict[(arg2Type, arg2Val)] != (arg1Type, arg1Val):
                return False, {}
            elif (arg2Type, arg2Val) not in predArgsDict.keys():
                predArgsDict[(arg2Type, arg2Val)] = (arg1Type, arg1Val)
        elif arg1Type == 'VARIABLE' and arg2Type == 'CONSTANT':
            if (arg1Type, arg1Val) in predArgsDict.keys() and predArgsDict[(arg1Type, arg1Val)] != (arg2Type, arg2Val):
                return False, {}
            elif (arg1Type, arg1Val) not in predArgsDict.keys():
                predArgsDict[(arg1Type, arg1Val)] = (arg2Type, arg2Val)
        elif arg1Type == 'VARIABLE' or arg2Type == 'VARIABLE':
            predArgsDict[(arg1Type, arg1Val)] = (arg2Type, arg2Val)
        elif arg1Type == 'CONSTANT' and arg2Type == 'CONSTANT' and arg1Val != arg2Val:
            return False, {}
    return True, predArgsDict


def isPredAndNegPredPresent(sentence):
    sentencePredicates = sentence.replace(" ", "").split("|")
    for i in range(len(sentencePredicates)):
        predicate1 = sentencePredicates[i]
        for j in range(i + 1, len(sentencePredicates)):
            predicate2 = sentencePredicates[j]
            if "~" in predicate1:
                if predicate1 == "~" + predicate2:
                    return True
            elif "~" in predicate2:
                if predicate2 == "~" + predicate1:
                    return True
    return False


lineNo = 1
isResolvalble = False


def resolutionCore(KB, query):
    global isResolvalble
    global loopStack
    queryPredicates = query.replace(" ", "").split("|")
    neqQueryLineNos = []
    for queryPredicate in queryPredicates:
        neqQueryLineNos.append(negPredList(queryPredicate, KB))
    if not neqQueryLineNos:
        return
    for i in range(len(queryPredicates)):
        queryPredicate = queryPredicates[i]
        queryPredName = getPredicateName(queryPredicate)
        for negatedPredicate in neqQueryLineNos:
            for lineNo in negatedPredicate:
                kbSentence = KB[lineNo]
                kbSentencePredicates = kbSentence.replace(" ", "").split("|")
                for kbSentencePredicate in kbSentencePredicates:
                    kbSentencePredicateName = getPredicateName(kbSentencePredicate)
                    if "~" in queryPredName:
                        negatedQueryPred = queryPredName.replace("~", "")
                    else:
                        negatedQueryPred = "~" + queryPredName
                    if negatedQueryPred == kbSentencePredicateName:
                        if isUnificationAllowed(queryPredicate, kbSentencePredicate):
                            isUnifiable, unificationDict = predicateMatching(queryPredicate, kbSentencePredicate)
                            if isUnifiable:
                                newQueryPredicatesList = copyList(queryPredicates)
                                newQueryPredicatesList.remove(queryPredicate)
                                newKbSentencePredList = copyList(kbSentencePredicates)
                                newKbSentencePredList.remove(kbSentencePredicate)
                                sentenceAftResolution = list(
                                    set(set(newQueryPredicatesList).union(newKbSentencePredList)))
                                if not sentenceAftResolution:
                                    isResolvalble = True
                                    return True
                                unifiedSentenceAftResol = unifyKbSentence("|".join(sentenceAftResolution),
                                                                          unificationDict)

                                if (queryPredicate, kbSentence, kbSentencePredicate) not in loopStack:
                                    if not isPredAndNegPredPresent(unifiedSentenceAftResol):
                                        loopStack.append((queryPredicate, kbSentence, kbSentencePredicate))
                                        resolutionCore(KB, unifiedSentenceAftResol)
                                if isResolvalble:
                                    return
    return


def standardiseVariable(sentence, line):
    result = []
    sentencePredicates = sentence.split("|")
    for predicate in sentencePredicates:
        predicateArguments = parseArgsInPred(getArgsList(predicate))
        newArgs = []
        for (elementType, elementValue, elementLexpos) in predicateArguments:
            if elementType == 'VARIABLE':
                elementValue = elementValue + str(line)
            newArgs.append(elementValue)
        newArgsSentence = ", ".join(newArgs)
        result.append(getPredicateName(predicate) + "(" + newArgsSentence + ")")
    return "|".join(result)


def createnewKB():
    KB = {}
    for key in kb_Dict.keys():
        KB[key] = kb_Dict[key]
    return KB


def mainResolutionMethod(kb, queries):
    global isResolvalble
    global loopStack
    global lineNo
    for i in range(len(kb)):
        kbSentence = kb[i]
        kbSentence = standardiseVariable(kbSentence, lineNo)
        kb_Dict[lineNo] = kbSentence
        lineNo = lineNo + 1

    for i in kb_Dict.keys():
        kb_sentence = parseSentence(kb_Dict[i], 0)
        # checking if the sentence has single predicate and if it is true
        if len(kb_sentence) <= 2 and kb_sentence:
            truePredicateDict[i] = kb_Dict[i]
    newKb = createnewKB()
    ii = 1
    with open('output.txt', 'w+') as outputFile:
        for query in queries:
            loopStack = []
            tempKbForEachQuery = {}
            isResolvalble = False
            if "~" in query:
                query = query.replace("~", "")
            else:
                query = "~" + query
            tempKbForEachQuery = createnewKB()
            tempKbForEachQuery[len(tempKbForEachQuery.keys()) + 1] = query
            listsinKBbyLength = sorted(newKb.values(), key=len)
            for i in range(1, len(newKb.keys()) + 1):
                tempKbForEachQuery[i] = listsinKBbyLength[i - 1]
            loopStack.append(query)
            resolutionCore(tempKbForEachQuery, query)
            ii = ii + 1
            outputFile.write(isResolvalble.__str__().upper())
            outputFile.write('\n')


def readInputData():
    kb = []
    queries = []
    with open('input.txt') as inputFile:
        input = inputFile.read().splitlines()
    number_of_queries = int(input[0])
    for i in range(1, number_of_queries + 1):
        queries.append(input[i])
    number_of_kb_sentence = int(input[number_of_queries + 1])
    input = input[number_of_queries + 2:]
    for i in range(number_of_kb_sentence):
        kb.append(input[i])
    mainResolutionMethod(kb, queries)

readInputData()