import re

class Measure:
	"""Class that stores information about a measure in the score"""
	def __init__(self, ncount, ntype, time):
		self.ncount = ncount
		self.ntype = ntype
		self.time = time
		self.type = "measure"
	def __str__(self):
		return "(" + str(self.ncount) + "/" + str(self.ntype) + ")"

class Note:
	"""Class that stores information about a note in the score"""
	def __init__(self, value, duration, time):
		self.value = value
		self.duration = duration
		self.time = time
		self.type = "note"
	def __str__(self):
		return str(self.value)

class Rest:
	"""Class that stores information about a rest in the score"""
	def __init__(self, duration, time):
		self.duration = duration
		self.time = time
		self.type = "rest"
	def __str__(self):
		return "R"

class VoiceChord:
	"""Class that stores information about chord performed by a single voice"""
	def __init__(self, notes, duration, time):
		self.notes = notes
		self.duration = duration
		self.time = time
		self.type = "vchord"
	def __str__(self):
		ret_str = ""
		first = True
		for n in self.notes:
			if first:
				ret_str += str(n)
				first = False
			else:
				ret_str += "/" + str(n) 
		return "{" + ret_str + "}"


class Chord:
	"""Class that stores information about a chord in the score"""
	def __init__(self, time, name):
		self.name = name
		self.time = time

	def __str__(self):
		return self.name

class PassingNote:
	"""Class that stores information about an error in the score"""
	def __init__(self, voice, time):
		self.voice = voice
		self.time = time

	def __str__(self):
		return "Voice: " + str(self.voice) + ", " + str(self.time)

class Error:
	"""Class that stores information about a passing note in the score"""
	def __init__(self, voice, time):
		self.voice = voice
		self.time = time

	def __str__(self):
		return "Voice: " + str(self.voice) + ", " + str(self.time)

class HaspSolution:
	"""Class that stores information of a single solution of the harmony
	deducing module"""
	def __init__(self, chords, voices, errors, passing, optimization):
		self.chords = chords
		self.voices = voices
		self.errors = errors
		self.passing = passing
		self.optimization = optimization

	def __str__(self):
		ret = "Chords: ["
		first = True
		for ch in self.chords:
			if first:
				first = False
				ret += str(ch)
			else:
				ret +=", " + str(ch)
		ret += "]\n"
		if len(self.errors) > 0:
			ret += "Errors: "
			first = True
			for er in self.errors:
				if first:
					first = False
					ret += str(er)
				else:
					ret +=" // " + str(er)
			ret += "\n"
		if len(self.passing) > 0:
			ret += "Passing Notes: "
			first = True
			for pn in self.passing:
				if first:
					first = False
					ret += str(pn)
				else:
					ret +=" // " + str(pn)
			ret += "\n"
		for voice in self.voices.keys():
			notes = self.voices[voice]
			ret += "Voice " + str(voice) + ": ["
			first = True
			for note in notes:
				if first:
					first = False
					ret += str(note)
				else:
					ret += ", " + str(note)
			ret += "]\n"
		ret += "OPT: " + str(self.optimization)
		return ret

class ClaspResult:
	"""Class that parses and stores output of a clasp execution
	It's created with the textual output of clasp and then stores
	satisfability, optimization status and all of it's solutions
	with its optimization values"""
	def __init__(self, asp_out):
		self.raw_output = asp_out
		self.solutions = self.parse_solutions()

	def parse_solutions(self):
		out = self.raw_output
		answers = re.split('Answer:\s*[0-9]+', out)
		solutions = []
		for ans in answers:
			if len(ans) > 0:
				try:
					figures = re.findall('out_figure\(([0-9]+),([0-9]+),([0-9]+),([0-9]+)\)', ans)
					figures = [(int(v),int(n),int(d),int(b)) for v,n,d,b in figures]
					figures = sorted(figures, key = lambda x: (x[0], x[3]))
					voices = {}
					i = 0
					acum_chord = []
					append_chord = False
					for figure in figures:
						if (figure[1] != -1):
							act_note = Note(int(figure[1]),int(figure[2]),int(figure[3]))
							if i < (len(figures)-1):
								next_fig = figures[i+1]
								if next_fig[0] == figure[0]:
									if next_fig[3] == figure[3]:
										acum_chord += [act_note]
									elif len(acum_chord) > 0 and next_fig[3] != figure[3]:
										acum_chord += [act_note]
										act_chord = VoiceChord(acum_chord,int(figure[2]),int(figure[3]))
										append_chord = True
							if (int(figure[0]) in voices.keys()):
								if append_chord:
									voices[int(figure[0])].append(act_chord)
									append_chord = False
									acum_chord = []
								elif len(acum_chord) == 0:
									voices[int(figure[0])].append(act_note)
							else:
								if append_chord:
									voices.update({(int(figure[0])) : [act_chord]})
									append_chord = False
									acum_chord = []
								elif len(acum_chord) == 0:
									voices.update({(int(figure[0])) : [act_note]})
							print append_chord

						else:
							act_rest = Rest(int(figure[1]),int(figure[3]))
							if (int(figure[0]) in voices.keys()):
								voices[int(figure[0])].append(act_rest)
							else:
								voices.update({(int(figure[0])) : [act_rest]})									
						i += 1

					measures = re.findall('real_measure\(([0-9]+),([0-9]+),([0-9]+)\)', ans)

					for measure in measures:
						for key in voices.keys():
							voices[key].append(Measure(int(measure[0]), int(measure[1]), int(measure[2])))

					voices = {k: sorted(v, key=lambda tup: tup.time) for k, v in voices.items()}

					chords = [Chord(int(ch[0]),ch[1]) for ch in sorted(re.findall('chord\(([0-9]+),([ivxmo7]+)\)', ans))]
					errors = [Error(int(er[0]),int(er[1])) for er in re.findall('out_error\(([0-9]+),([0-9]+)\)', ans)]
					passing = [PassingNote(int(pn[0]),int(pn[1])) for pn in re.findall('passing_note\(([0-9]+),([0-9]+)\)', ans)]
					str_opts = re.split("\s*", re.search('Optimization:((?:\s*[0-9]+)+)', ans).group(1))
					taw = str_opts.pop(0)
					optimums = map(int, str_opts)
					solutions += [HaspSolution(chords,voices,errors,passing,optimums)]
				except AttributeError:
					print "Discarding incomplete answer due to early temrination."
		return solutions

	def __str__(self):
		ret = ""
		ansno = 1
		for sol in self.solutions:
			ret += "Answer " + str(ansno) + ":\n"
			ret += str(sol) + "\n"
			ansno += 1
		return ret