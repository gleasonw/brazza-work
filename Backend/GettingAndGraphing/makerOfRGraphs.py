import csv
import rpy2.robjects as robjects
import shutil
import os

from rpy2.robjects.packages import importr

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

class GallicaGrapher:
    def __init__(self, csvFile, tenMostPapers, graphSettings):
        self.fileName = csvFile
        self.graphFileName = ''
        self.tenMostPapers = tenMostPapers
        self.settings = graphSettings
        self.theCSVforR = None
        self.ggplotForR = None
        self.breakLength = 360
        self.directory = os.path.dirname(os.path.abspath(__file__))

    @staticmethod
    def arrangeGGplotsAndPlot(listOfGGplots, fileName):
        fileName = fileName.replace(".csv",".png")
        grdevices = importr('grDevices')
        grdevices.png(file=fileName, width=1920, height=1080)
        robjects.r('''
        graphMulti <- function(listOfGGplots){
            numberPlots <- length(listOfGGplots)
            nrows <- floor(sqrt(numberPlots))
            do.call("grid.arrange", c(listOfGGplots, nrow=nrows))
        }
        ''')
        multiGraph = robjects.globalenv["graphMulti"]
        multiGraph(listOfGGplots)
        grdevices.dev_off()
        directory = os.path.dirname(os.path.abspath(__file__))
        shutil.move(fileName, os.path.join("../Graphs", fileName))


    def getGGplot(self):
        return self.ggplotForR


    def parseGraphSettings(self):
        self.makeGraphFileName()
        self.readCSVtoR()
        if self.settings["graphType"] == "stackedBar":
            self.establishTopPapers()
            self.tenMostPapers = self.transformTopTenPapersToRVector()
            self.makeStackedBarGraph()
        elif self.settings["graphType"] == "bar":
            self.makeBarGraph()
        elif self.settings["graphType"] == "percentBar":
            self.establishTopPapers()
            self.tenMostPapers = self.transformTopTenPapersToRVector()
            self.makePercentBar()
        elif self.settings["graphType"] == "freqPoly":
            self.makeFreqPoly()
        elif self.settings["graphType"] == "multiFreqPoly":
            self.makeMultiFreqPoly()
        elif self.settings["graphType"] == "density":
            self.makeDensityGraph()
        else:
            pass


    def establishTopPapers(self):
        if len(self.tenMostPapers) == 0:
            dictionaryFile = "{0}-{1}".format("TopPaperDict", self.fileName)
            with open(os.path.join("../CSVdata", dictionaryFile)) as inFile:
                reader = csv.reader(inFile)
                for newspaper in reader:
                    thePaper = newspaper[0]
                    self.tenMostPapers.append(thePaper)

    def readCSVtoR(self):
        zoo = importr('zoo')
        base = importr('base')
        dplyr = importr('dplyr')
        stringr = importr('stringr')
        scales = importr('scales')
        lubridate = importr('lubridate')
        tibble = importr('tibble')
        grids = importr('gridExtra')
        ggplot2 = importr('ggplot2')
        utils = importr('utils')
        self.theCSVforR = utils.read_csv(os.path.join("../CSVdata", self.fileName), encoding="UTF-8", stringsAsFactors=False, header=True)
        self.theCSVforR = self.parseDateForRCSV()

    def makeStackedBarGraph(self):
        self.theCSVforR = self.createFillColumnForRCSV()

        robjects.r('''
        initiateStackedBarGGplot <- function(dataToGraph){
            graphOfHits <- ggplot(dataToGraph, aes(x=numericDate, ..count.., fill=fillPaper)) +
                geom_histogram(binwidth=120)
                colors = c("#e6beff", "#9a6324", "#fffac8", "#800000", "#aaffc3", "#808000", "#ffd8b1", "#000075", "#808080", "#ffffff", "#000000")
                scale_fill_manual(values = colors)
            return(graphOfHits)
        }
        ''')

        ggplotInitiate = robjects.globalenv['initiateStackedBarGGplot']
        self.ggplotForR = ggplotInitiate(self.theCSVforR)
        graphTitle = self.makeSingleGraphTitle()
        self.ggplotForR = self.addLabelsToGGplot(graphTitle)

    def makeDensityGraph(self):
        self.theCSVforR = self.createFillColumnForRCSV()
        robjects.r('''
        initiateDensityGGplot <- function(dataToGraph){
            graphOfHits <- ggplot(dataToGraph, aes(x=numericDate, ..count.., fill=fillPaper)) +
                geom_density(position="stack")
                colors = c("#e6beff", "#9a6324", "#fffac8", "#800000", "#aaffc3", "#808000", "#ffd8b1", "#000075", "#808080", "#ffffff", "#000000")
                scale_fill_manual(values = colors)
            return(graphOfHits)
        }
        ''')

        ggplotInitiate = robjects.globalenv['initiateDensityGGplot']
        self.ggplotForR = ggplotInitiate(self.theCSVforR)
        graphTitle = self.makeSingleGraphTitle()
        self.ggplotForR = self.addLabelsToGGplot(graphTitle)

    def makeFreqPoly(self):
        robjects.r('''
        initiateFreqPolyGGplot <- function(dataToGraph){
            graphOfHits <- ggplot(dataToGraph, aes(x=numericDate, ..count..)) +
                geom_freqpoly(binwidth=30) +
                scale_y_continuous()
            return(graphOfHits)
        }
        ''')

        freqPolyInitiate = robjects.globalenv['initiateFreqPolyGGplot']
        self.ggplotForR = freqPolyInitiate(self.theCSVforR)
        graphTitle = self.makeSingleGraphTitle()
        self.ggplotForR = self.addLabelsToGGplot(graphTitle)

    def makeMultiFreqPoly(self):
        robjects.r('''
        initiateManyFreqPolyGGplot <- function(dataToGraph){
            graphOfHits <- ggplot(dataToGraph, aes(x=numericDate, colour=term)) +
                geom_freqpoly(binwidth=120)
            return(graphOfHits)
        }
        ''')

        initiateManyFreqPoly = robjects.globalenv['initiateManyFreqPolyGGplot']

        self.ggplotForR = initiateManyFreqPoly(self.theCSVforR)
        graphTitle = self.graphFileName
        self.ggplotForR = self.addLabelsToGGplot(graphTitle)

    def makeBarGraph(self):

        robjects.r('''
        initiateBarGGplot <- function(dataToGraph){
            graphOfHits <- ggplot(dataToGraph, aes(x=numericDate, ..count..)) +
                geom_histogram(binwidth=30)
            return(graphOfHits)
        }
        ''')

        initiateBar = robjects.globalenv['initiateBarGGplot']
        self.ggplotForR = initiateBar(self.theCSVforR)
        graphTitle = self.makeSingleGraphTitle()
        self.ggplotForR = self.addLabelsToGGplot(graphTitle)

    def makePercentBar(self):
        self.theCSVforR = self.createFillColumnForRCSV()
        robjects.r('''
        initiatePercentGGplot <- function(dataToGraph){
            graphOfHits <- ggplot(dataToGraph, aes(x=numericDate,..count.., fill=fillPaper)) +
                        geom_histogram(binwidth=30, position="fill")
            return(graphOfHits)
        }
        ''')

        initiateBar = robjects.globalenv['initiatePercentGGplot']
        self.ggplotForR = initiateBar(self.theCSVforR)
        graphTitle = self.makeSingleGraphTitle()
        self.ggplotForR = self.addLabelsToGGplot(graphTitle)

    def addLabelsToGGplot(self, title):
        robjects.r('''
            labelAdder <- function(theGGplot, title, csvResults, breakLength){
                seqForLabels <- seq(min(csvResults$num)-15,max(csvResults$num),breakLength)
                seqForLabels <- as_date(seqForLabels)
                seqForLabels <- format(seqForLabels, "%b %Y")
                theGGplot <- theGGplot + scale_x_continuous(breaks = seq(min(csvResults$numericDate)-15,max(csvResults$numericDate),breakLength),
                                            minor_breaks = seq(min(csvResults$num)-15,max(csvResults$num),30),
                                            labels = seqForLabels)
                theGGplot <- theGGplot + labs(title=title, x="Year/month", y="occurrence count")
                theGGplot <- theGGplot + theme(axis.text = element_text(size=12), axis.text.x = element_text(angle = 45, hjust = 1))
            }
        ''')
        labelAdder = robjects.globalenv['labelAdder']
        return labelAdder(self.ggplotForR, title, self.theCSVforR, self.breakLength)

    def parseDateForRCSV(self):
        robjects.r('''
            parseDate <- function(csvResults){ 
                csvResults <- csvResults %>% mutate(date=ymd(date))
                csvResults <- csvResults %>% mutate(date=floor_date(date, "months"))
                csvResults <- csvResults %>% mutate(numericDate = as.numeric(date))
                return(csvResults)
                }
            ''')
        mutateFunction = robjects.globalenv['parseDate']
        return mutateFunction(self.theCSVforR)


    def createFillColumnForRCSV(self):
        robjects.r('''
            createFillColumn <- function(csvResults, paperVector){
                csvResults <- csvResults %>% mutate(fillPaper=ifelse(journal %in% paperVector, journal, 'Other')) 
            }
        ''')
        createFillColumn = robjects.globalenv['createFillColumn']
        return createFillColumn(self.theCSVforR, self.tenMostPapers)

    def transformTopTenPapersToRVector(self):
        robjects.r('''
            ListToVector <- function(listOfPapers){
                paperVector <- unlist(listOfPapers,recursive=TRUE)
                return(paperVector)
            }
        ''')
        vectorTransform = robjects.globalenv['ListToVector']
        return vectorTransform(self.tenMostPapers)

    def plotGraphAndMakePNG(self):
        grdevices = importr('grDevices')
        grdevices.png(file=os.path.join(self.directory, self.graphFileName), width=1920, height=1080)
        robjects.r('''
            graphThatGGplot <- function(theGraph){
                plot(theGraph)
            }
            '''
        )
        dataGrapher = robjects.globalenv['graphThatGGplot']
        dataGrapher(self.ggplotForR)
        grdevices.dev_off()
        shutil.move(self.graphFileName, os.path.join("../Graphs", self.graphFileName))


    def makeGraphFileName(self):
        self.graphFileName = self.fileName[0:len(self.fileName)-4]
        self.graphFileName = "{0}-{1}".format(self.graphFileName, self.settings["graphType"])
        self.graphFileName = self.graphFileName + ".png"

    def makeSingleGraphTitle(self):
        titleSplit = self.fileName.split("--")
        searchTermProbably = titleSplit[0]
        graphTitle = "{0} usage by year/mon".format(searchTermProbably)
        return graphTitle







