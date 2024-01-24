from binaryninja import *
import time


def add_tags(bv):
    bv.create_tag_type("XOR", "⊕")
    bv.create_tag_type("XOR_data", "!⊕")


class XORFinder(BackgroundTaskThread):
    def __init__(self, bv, data):
        BackgroundTaskThread.__init__(self, "Looking for xor...", True)
        self.bv = bv
        self.data = data

    def run(self):
        add_tags(self.bv)
        if self.data:
            self.run_data()
        else:
            self.run_dumb()


    def run_dumb(self):
        for f in self.bv.functions:
            for bb in f.basic_blocks:
                for dt in bb.get_disassembly_text():
                    if dt.tokens[0].text == 'xor':
                        # Cleaning XOR operation that results in 0
                        if dt.tokens[2].value != dt.tokens[4].value:
                            self.bv.add_tag(dt.address, "XOR", "XOR instruction")
                            binaryninja.log_info(
                                "FOUND XOR operation at {}".format(hex(dt.address)))

    def run_data(self):
        for data_var in self.bv.data_vars:
            # Get references for the current data_var
            data_var_references = list(self.bv.get_code_refs(data_var))
            # Need to check if there is at least one reference
            if data_var_references:
                for ref in data_var_references:
                    # These can crash, if function have not been analysed yet, the llil will fail.
                    try:
                        rllil = ref.llil
                    except:
                        binaryninja.log_error("Cannot get llil for {}".format(ref))
                        continue
                    if not rllil:
                        continue
                    if len(rllil.operands) == 2:
                        if not type(ref.llil.operands[1]) is dict:
                            if ref.llil.operands[1].operation == LowLevelILOperation.LLIL_XOR:
                                self.bv.add_tag(ref.address, "XOR_data", "XOR instruction with initialized memory data")
                                binaryninja.log_info(
                                    "FOUND XOR operation on {} at {}".format(hex(data_var), hex(ref.address)))

def find_xor(bv):
    x = XORFinder(bv,False)
    x.start()

def find_xor_data(bv):
    x = XORFinder(bv,True)
    x.start()


PluginCommand.register("XOR finder\\ Dumb mode", "Find and tag all xor operations", find_xor)
PluginCommand.register("XOR finder\\ With data", "Find and tag all xor operations that involve initialized data", find_xor_data)
