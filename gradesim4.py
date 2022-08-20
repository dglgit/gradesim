from collections import defaultdict
import copy
import json

DOC=\
'''
gradesim: 4th version of a grade simulator to see what would happen to your grade if you did bad on a test or something
also does algebra to figure out minimum score you need to maintain a certain grade(untested)

Grade class:
    __init__(score, total, name='')->
        score: score you got on an assignemnt
        total: max score you couldve gotten on that assignment
        name: optional; name of assignment
    percentage()-> gets percent of grade[0,1]
    minimumPerfect(threshold): minimum max(m/m) score of an assignment that you get 100% on needed to keep your grade above a certain threshold

'''

m='m'
p='p'
WEIGHTS={'m':.7,'p':.3}
apchem={'m':.4,'labs':.25}
UNCONTRACT=defaultdict(lambda x: x,{'m':'mastery','p':'progression','e':'engagement'})
NULLDICT=defaultdict(lambda x: x)
def acronym(s):
    return ''.join([i[0] for i in s.lower().split(' ')])
class Grade:
    def __init__(self, score:int, total:int, name=''):
        self.score=score
        self.total=total
        self.name=name
    def percentage(self) -> float:
        return self.score/self.total
    def __add__(self, other):
        return Grade(self.score+other.score, self.total+other.total,name=self.name)
    def __iadd__(self, other):
        self.score+=other.score
        self.total+=other.total
        return self
    def toStr(self):
        info=f"{self.score}/{self.total}"
        if not self.isempty():
            info+=f', {self.percentage()*100}%'
        else:
            info+=', N/A'
        if self.name=='':
            return f'Grade: {info}'
        else:
            return f'{self.name}: {info}'
    def __str__(self):
        return self.toStr()
    def __repr__(self):
        return str(self)
    def __radd__(self,other):
        #assumes this is for sum() list of Grades and assuming it does like
        #result=0
        #for i in list: result+=Grade
        return self
    def isempty(self) -> bool:
        return self.score==0 and self.total==0
    def minimumPerfect(self, threshold) -> float:
        return (self.score-threshold*self.total)/(threshold-1)
    def minimumScore(self, threshold, maxScore) -> float:
        return threshold*(self.total+maxScore)-self.score
    def toDict(self):
        return {'score':self.score,'total':self.total}
    
    
class Course:
    def __init__(self, name:str='',grades=None,assignments=None,weights:dict=WEIGHTS, uncontractions=UNCONTRACT):
        self.weights=weights
        self.uncontractions=uncontractions
        #maybe key the weights with the acronyms and have the user initialize with actual words like "mastery" instead of m and convert it to m later
        if grades is None:
            self.grades={w:Grade(0,0, uncontractions[w]) for w in weights}
        else:
            self.grades=grades
        if assignments is None:
            #maybe list of assignments(named grades)
            self.assignments={w:[Grade(self.grades[w].score, self.grades[w].total,'unnamed')] for w in weights}
        else:
            self.assignments=assignments
        self.name=name
    def percentage(self):
        res=0
        denom=0
        for w in self.weights:
            if not self.grades[w].isempty():
                res+=self.grades[w].percentage()*self.weights[w]
                denom+=self.weights[w]
        if denom==0:
            return float('nan')
        return res/denom
    def updateGrade_(self, category:str, grade:Grade):
        #inplace operation
        if grade.name:
            self.assignments[category].append(grade) 
        else:
            self.assignments[category][0]+=grade
        self.grades[category]+=grade
    def updateGrade(self, category:str, grade:Grade):
        #returns new Grade object
        copyGrades=copy.deepcopy(self.grades)
        copyGrades[category]+=grade
        ret=Course(name=self.name, grades=copyGrades, weights=self.weights, uncontractions=self.uncontractions)
        return ret
    def lsAssignments(self):
        header=f'{self.name} '+'{' if self.name else "Course: {"
        header+='\n'
        for w in self.grades:
            header+=f'\t({self.weights[w]}) {str(self.grades[w])}, {str(self.assignments[w])}\n'
        header+=f'\toverall: {self.percentage()*100}%\n\tid: {id(self)}\n'
        header+='}'
        return header
    def __str__(self):
        header=f'{self.name} '+'{' if self.name else "Course: {"
        header+='\n'
        for w in self.grades:
            header+=f'\t({self.weights[w]}) '+str(self.grades[w])+'\n'
        header+=f'\toverall: {self.percentage()*100}%\n\tid: {id(self)}\n'
        header+='}'
        return header
    def minimumPerfect(self, threshold, category):
        totes=0
        tdenom=0
        for w in self.weights:
            if w!=category:
                totes+=self.grades[w].percentage()*self.weights[w]
                tdenom+=self.weights[w]
        c=threshold-totes/tdenom
        return self.grades[category].minimumPerfect(c/self.weights[category])
    def minimumScore(self, threshold,category, total):
        totes=0
        tdenom=0
        for w in self.weights:
            if w!=category:
                totes+=self.grades[w].percentage()*self.weights[w]
                tdenom+=self.weights[w]
        c=threshold-totes/tdenom
        return self.grades[category].minimumScore(c/self.weights[category],total)
    def toDict(self):
        #
        '''
        ideally should be like
        $course-name: {
            $category-name:{
                weighting: $weight
                assignments: [
                    $grade-name: {
                        score: $score
                        total: $total
                    }
                    ... 
                ]
                score: $score
                total: $total
            }
        }
        '''
        ret={}
        for w in self.weights:
            sub={'weighting':self.weights[w]}
            sub.update(self.grades[w].toDict())
            assignments={g.name:g.toDict() for g in self.assignments[w]}
            sub.update({'assignments':assignments})
            ret.update({w:sub})
        return ret
        
    def readFile(fname)->dict:
        #if ret has 1 element just return that one element
        ret={}
        with open(fname,'r') as ff:
            d=json.load(ff)
            print(d)
            for course_name in d:
                course=d[course_name]
                print(course)
                weights={}
                assignments={}
                grades={}
                for cat in course:#grade category
                    category=course[cat]
                    weights[cat]=category['weighting']
                    g=category['assignments']
                    assignments[cat]=[Grade(g[name]['score'],g[name]['total'],name) for name in category['assignments']]
                    grades[cat]=Grade(category['score'],category['total'],cat)
                ret[course_name]=Course(name=course_name, grades=grades, assignments=assignments)
            return ret


        pass
def courseToFile(cs:list, fname:str):
    with open(fname,'w') as ff:
        dicts={c.name:c.toDict() for c in cs}
        json.dump(dicts,ff)

    
def test():
    prefix='grade-data/'
    g=Grade(0,0)
    g+=Grade(5,7)
    #print(g)
    c=Course('chemistry')
    c.updateGrade_('m',Grade(80,100, 'naming'))
    c.updateGrade_('m',Grade(98.6,100, 'solutions'))
    c.updateGrade_('p',Grade(100,100,'lab'))
    print('first: ')
    print(c.lsAssignments())
    courseToFile([c],prefix+'c1.grade')
    print('read: ')
    print(Course.readFile(prefix+'c1.grade')['chemistry'].lsAssignments())

    c.updateGrade_('m',Grade(80,100,'test1'))
    c.updateGrade_('m',Grade(90,110,'test3'))
    c.updateGrade_('p',Grade(100,100,'test2'))
    print(c.lsAssignments())
    print(c.updateGrade('m', Grade(90,100)))
    print(sum([Grade(3,4),Grade(40,43),Grade(30,32)]).percentage())
test()
