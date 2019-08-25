import asyncio
import json
import traceback


class IdNotFound(Exception):
	pass


class FpNotFound(IdNotFound):
	def __init__(self, fp: str):
		self.fp = fp

	def __str__(self):
		return f"FpNotFound: {self.fp} was not found and create was not enabled!"

	def __int__(self):
		return 404

class AHM:
	def __init__(self, run: bool = None):
		self.running = run

	def __bool__(self):
		return self.running


async def async_handle_modify(fp: str, newdata: dict, indent=2, *, backup: bool=False):
	"""A none-blocking version of `handle_modify`. does the same thing but waits if a write was done recently"""
	while bool(AHM):
		await asyncio.sleep(5)

	if backup:
		with open(fp, 'r') as back:
				hackup=json.load(back)
	try:
		with open(fp, 'w') as alafile:
			try:
				json.dump(newdata, alafile, indent=indent)
				return True
			except:
				json.dump(hackup, alafile, indent=indent)
				raise
	except:
		return traceback.format_exc()


def handle_modify(fp: str, newdata: dict, indent=2, *, backup: bool=False):
	if backup:
		with open(fp, 'r') as back:
				hackup=json.load(back)
	try:
		with open(fp, 'w') as alafile:
			try:
				json.dump(newdata, alafile, indent=indent)
				return True
			except:
				json.dump(hackup, alafile, indent=indent)
				raise
	except:
		return traceback.format_exc()


def write(fp: str, newdata: dict, indent=2, *, backup: bool=False):
	"""just an alias for ``handle_modify``"""
	handle_modify(fp, newdata, indent, backup=backup)


def read(fp):
	try:
		with open(fp, 'r') as alafile:
			try:
				z = json.load(alafile)
				return z
			except:
				return traceback.format_exc()
	except:
		return traceback.format_exc()

async def find(fp, *, in_key: str, thing):
	with open(fp, 'r') as tofind:
		data = json.load(tofind)
		if data:
			if in_key in data.keys():
				if thing in data[in_key].keys():
					return data[in_key][thing]
			else:
				raise IdNotFound(f"{in_key} not found in {data}")


def format(fp: str, *, data: dict, indents: int = 0, create: bool = True):
	"""
	format a file, ready for modifying
	WARNING: THIS WILL OVERWRITE ANY EXISTING DATA
	:param fp:
	:param data:
	:param indents:
	:return:
	"""
	if create:
		mode = 'w+'
	else:
		mode = 'w'
	with open(fp, mode) as file:
		file.write('{}')
		json.dump(data, file, indent=indents)
	return
