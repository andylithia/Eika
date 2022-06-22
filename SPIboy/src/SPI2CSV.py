class SPI2CSV:
    
    def __init__(self, spiParam:dict, cmdDict:dict, regDict:dict) -> None:
        """
        SPI Interface Init
        Keyword arguments:
        :spiParam: A dictionary of spi parameters
        :cmdParam: A dictionary of spi commands
                    {
                        Command Name (str) : Command (int),
                        ... 
                    }
        :regDict:  A dictionary of SPI Addr <-> Physical Register 
                    {
                        Reg Name (str) : [
                            [ACACIA Address (int), rw (str), base (int), wordsize (int)],
                            [SPI Address (int),    rw (str), base (int), wordsize (int)],
                            Comment (str),
                            Omit Config (int
                                The omit config is useful for documentation
                                It allows you to omit parts of the dictionary when printing out
                                bit 0 = Omit All
                                bit 1 = Omit Comment
                                )
                        ],
                        ...
                    }
        :return:   None
        """
        self.spiParam = spiParam;
        self.cmdDict  = cmdDict;
        self.regDict  = regDict;
        self.oBuf = []
        # pinState also deals with RST & CE, but not clk
        self.pinState = {\
            self.spiParam['rst_pin']: False,
            self.spiParam['ce_pin']: False
            }
        for pin in self.spiParam['other_pins']:
            self.pinState[pin] = False

        pass

    def i2hexStr(self, i:int) -> str:
        """
        i2hexStr: Convert integer to hexadecimal string
        The word size & bit order are configured in self.spiParam
        :i:      Input integer
        :return: The hexadecimal string
        """
        b = i;
        if(self.spiParam['LSBfirst']):
            b = '{:0{width}b}'.format(b, width=self.spiParam['wordsize'])
            b = int(b[::-1], 2)
        return '0x{:0{width}X}'.format(b, width=self.spiParam['wordsize']>>2)

    def writeRegDict(self, fname: str, dict='', target='readable', omitEnable=False) -> str:
        from tabulate import tabulate
        # The tabulate library is used for pretty printing
        print('\'tabulate\' package loaded')
        import csv
        print('\'csv\' package loaded')

        if dict=='':
            d = self.regDict
        else:
            d = dict
        if target not in {'readable','csv'}:
            print('! Error: Unknown listing target: ', target)
            return
        
        f = open(fname,'w+', encoding='cp1252' ,newline="")
        if(not f):
            print('! Error: File open failed: ', fname)
            return
        
        lines = []
        lines_out = []
        firstrow = ['SPI\nAddress','Name','R/W','ACACIA\nAddress', 'ACACIA\nMask', 'SPI\nMask', 'HELP']
        for tag in d:
            mapped_acacia = True
            mapped_spi    = True
            ACACIA = d[tag][0]
            SPI    = d[tag][1]
            HELP   = d[tag][2]
            if(len(ACACIA)==0):
                ACACIA='N/A'
                mapped_acacia = False
                
            if(len(SPI)==0):
                SPI ='N/A'
                ida = 0xFFFF
                mapped_spi = False
            else:
                ida = int(SPI[0])
            omit_flag = d[tag][3]
            lines.append([ida, tag, ACACIA, SPI, HELP,mapped_acacia, mapped_spi, omit_flag])
        lines = sorted(lines)
        
        for line in lines:
            line_out = ['','','','','','','']
            addr_hex = '0x{:04X}'.format(line[0])
            line_out[0] = addr_hex
            line[0]     = addr_hex
            line_out[1] = line[1]
            mapped_acacia = line[5]
            mapped_spi    = line[6]
            if(not mapped_acacia):
                if(not mapped_spi):
                    print('! {:s} Both interfaces unmapped'.format(addr_hex))
                    continue
                else:
                    spi_lsb     = int(line[3][2])
                    spi_msb     = int(line[3][3])+spi_lsb-1
                    # SPI Mapped
                    line_out[2] = line[3][1] # R/W
                    line_out[3] = 'N/A'
                    line_out[4] = 'N/A'     # ACACIA Prop
                    line_out[5] = '[{:d}:{:d}]'.format(spi_msb,spi_lsb)
            else:
                acacia_addr = int(line[2][0])
                acacia_base = int(line[2][2])
                # acacia_word = acacia_base>>4 
                # acacia_lsb  = acacia_base%16
                # acacia_msb  = int(line[2][3])+acacia_lsb
                acacia_lsb  = acacia_base
                acacia_msb  = int(line[2][3])+acacia_lsb-1
                
                if(not mapped_spi):
                    # ACACIA Mapped
                    line_out[0] = 'N/A'
                    line_out[2] = line[2][1] # R/W
                    line_out[3] = '0x{:04X}'.format(acacia_addr)
                    line_out[4] = '[{:d}:{:d}]'.format(acacia_msb,acacia_lsb)
                    line_out[5] = 'N/A'      # SPI Prop
                else:
                    spi_lsb     = int(line[3][2])
                    spi_msb     = int(line[3][3])+spi_lsb
                    # Both Interfaces Mapped
                    if(line[2][1]!=line[3][1]):
                        print('! {:s} RW property mismatch between interfaces'.format(line[0]))
                        continue
                    if(line[2][3]!=line[3][3]):
                        print('! {:s} bitwidth property mismatch between interfaces'.format(line[0]))
                        continue
                    
                    line_out[2] = line[2][1] # R/W
                    line_out[3] = '0x{:04X}'.format(acacia_addr)
                    line_out[4] = '[{:d}:{:d}]'.format(acacia_msb,acacia_lsb)
                    line_out[5] = '[{:d}:{:d}]'.format(spi_msb,spi_lsb)
            line_out[6] = line[4]
            if(omitEnable):
                if(line[7]&0x01):
                    line_out[0] = '...'
                    line_out[1] = '...'
                if(line[7]&0x02):
                    line_out[6] = '...'
            lines_out.append(line_out)
        
        if(omitEnable):
            # Remove omitted lines
            line_purge_ff = False
            Count = 0
            lines_out1 = []
            for line in lines_out:
                if(line_purge_ff):
                    count = count+1
                    if(line[1]!='...'):
                        line_purge_ff = False
                        lines_out1.append(['','... ({:d} Registers Omitted) ...'.format(count),'','','','',''])
                        lines_out1.append(line)
                else:
                    if(line[1]=='...'):
                        count = 0
                        line_purge_ff = True
                    else:
                        lines_out1.append(line)
        
        if(target=='csv'):
            print('Writing CSV File...')
            writer = csv.writer(f)
            writer.writerow(firstrow)
            writer.writerows(lines_out1)
            
        elif(target=='readable'):
            print('Writing Human Readable File...')
            tabbed = tabulate(lines_out1,headers=firstrow, tablefmt='presto')
            f.writelines(tabbed)
        
        f.close()
        return lines

    # writers
    def flush(self) -> list:
        """
        flush: Cleaning the output buffer
        :return: a reference to the internal buffer
        """
        self.oBuf = []
        return self.oBuf

    # Internal Buffer Datatype
    # {{pins}, measure, repeat, sclk, chipID, command, payload, mask, comment, IDType}
    # {pins}:  Dictionary,  all the pin status
    #              If a pin is not in the dictionary or the dictionary is None
    #              it means that the pin should remain unchanged
    # measure: String,      which measurement sequence to run
    # repeat:  Depricated feature
    # sclk:    Integer, how many clock cycles to run
    # chipID:  Which chip is under test
    # command: Integer, command
    # Payload: Integer, data payload
    # Mask:    Integer, variable payload marker
    # comment String,  generic comment line
    # IDType:  1: 8-bit  addressing
    #          0: 32-bit addressing

    def w(self, id:int, cmd:str, data=0, mask=0, clkc=32, comment='', IDType=1) -> list:
        """
        w: write a command to the output buffer
        :param id:      Target Chip ID
        :param cmd:     Command to execute, should be a str-key in the cmdDict
        :param data:    The payload that follows the command, can be either a number or a str-key in the regDict
        :param mask:    Marking that some part of the output hexadecimal can be masked for variables
        :param clkc:    Change this for extra clock cycles, useful for things like reset delay
        :param comment: Some extra comments to make the output file readable
        :return: a reference to the internal buffer
        """
        lines = [{},{}]
        # Toggle CE pin
        lines[0]['pins'] = {self.spiParam['ce_pin']:not self.spiParam['ce_active_high']}
        lines[1]['pins'] = {self.spiParam['ce_pin']:    self.spiParam['ce_active_high']}

        # Populate the other pins
        for pin in self.pinState.keys():
            if pin not in lines[0]['pins'].keys():
                # Untouched Pin
                lines[0]['pins'][pin] = self.pinState[pin]
                lines[1]['pins'][pin] = self.pinState[pin]


        # Generate Clock
        if IDType==1:
            if clkc < 32:
                print('Warning: Clock cycle < 32 for ID Type 1');
        else:
            if clkc <64:
                print('Warning: Clock cycle < 64 for ID Type 0');

        lines[0]['sclk'] = '{:d} cycles'.format(clkc);
        lines[1]['sclk'] = self.spiParam['cidle']      # the clock stays idle 
        
        # Generate Data
        if(IDType==1):
            # 8-bit addressing
            lines[0]['chipID'] = id
        else:
            # 32-bit addressing
            lines[0]['chipID'] = id

        # Generate Command
        lines[0]['command'] = self.cmdDict[cmd]
        # Generate Data
        if type(data) is str:
            lines[0]['payload'] = self.regDict[data][1][0]
        elif type(data) is int:
            lines[0]['payload'] = data

        lines[0]['mask'] = mask
        lines[0]['comment'] = comment
        lines[0]['IDType']  = IDType
        
        self.oBuf = self.oBuf + lines
        return self.oBuf
    
    def showOBuf(self) -> list:
        print(self.oBuf)
        return self.oBuf

    def pinDeposit(self, pinDict:dict) -> list:
        for pin in pinDict:
            if pin not in self.pinState.keys():
                print('ERROR: pinDeposit touches undefined pin: {:s}'.format(pin))
            self.pinState[pin] = pinDict[pin]
        return self.pinState

    def wCommentLine(self, line:str) -> list:
        self.oBuf.append({'commentLine':line})
        return self.oBuf
    

    def __b10(self, i:bool,xnor:bool)->int:
        if i:
            if xnor:
                return 1
            else:
                return 0
        else:
            if xnor:
                return 0
            else:
                return 1

    def wReset(self, clkc:int=1300, comment:str='') -> list:
        lines = [{},{}]
        
        lines[0]['sclk'] = '{:d} cycles'.format(clkc);
        lines[1]['sclk'] = self.spiParam['cidle']      # the clock stays idle 
        
        lines[0]['comment'] = comment

        lines[0]['pins'] = {}
        lines[1]['pins'] = {}
        
        # Toggle CE pin
        lines[0]['pins'] = {\
            self.spiParam['ce_pin']: not self.spiParam['ce_active_high'],
            self.spiParam['rst_pin']:self.__b10(False, self.spiParam['rst_active_high'])}
        lines[1]['pins'] = {\
            self.spiParam['ce_pin']:    self.spiParam['ce_active_high'],
            self.spiParam['rst_pin']:self.__b10(True,  self.spiParam['rst_active_high'])}

        # Populate the other pins
        for pin in self.pinState.keys():
            if pin not in lines[0]['pins'].keys():
                # Untouched Pin
                lines[0]['pins'][pin] = self.pinState[pin]
                lines[1]['pins'][pin] = self.pinState[pin]

        self.oBuf = self.oBuf + lines
        return self.oBuf

    def writeCSV(self, fname:str) -> list:
        # import csv
        # We don't use the csv library
        rst_pinName = self.spiParam['rst_pin']
        ce_pinName  = self.spiParam['ce_pin']
        clk_pinName = self.spiParam['clk_pin']
        # Commit the internal buffer to a csv file
        # Generate the first row, GF SPI Test Format

        extPinList  = self.spiParam['other_pins']
        pinState = [0]*(len(extPinList)+2)
        firstRow = '{:s}'.format(rst_pinName)

        for pinID in range(len(extPinList)):
            # Populate the extra pins
            firstRow=firstRow+',{:s}'.format(extPinList[pinID])
        firstRow = firstRow + ',{:s},measure,repeat,{:s},din,mask,addr_type,CHIP ID,CMD,DATA,Comment\n'.format(ce_pinName,clk_pinName)
        oBuf_CSV = [firstRow]

    
        for line in self.oBuf :
            # For the pins, we won't do any logic here.
            # All pin toggling, keeping, etc are done in the SPI.w function
            if 'commentLine' in line:
                oline = line['commentLine']
            else:
                if  rst_pinName in line['pins']:
                    oline = '{:1d}'.format(self.__b10(line['pins'][rst_pinName],self.spiParam['rst_active_high']))
                else:
                    oline = ''

                for pin in extPinList:
                    if pin in line['pins']:
                        oline = oline + ',{:1d}'.format(self.__b10(line['pins'][pin],True))
                    else:
                        oline = oline + ','
                
                if ce_pinName in line['pins']:
                    oline = oline + ',{:1d}'.format(self.__b10(line['pins'][ce_pinName],self.spiParam['ce_active_high']))
                else:
                    oline = oline + ','

                for feature in ['measure', 'repeat', 'sclk']:
                    if feature in line.keys():
                        oline = oline + ',' + str(line[feature])
                    else:
                        oline = oline + ','
                
                # Construct DIN
                # TODO: Deal with 64-bit transactions
                if 'command' in line.keys():
                    if line['IDType']>1:
                        print('ERROR: addr_type too long')
                    if line['payload']>0xFFFF:
                        print('ERROR: payload too long')
                    if line['command']>0x7F:
                        print('ERROR: command too long')
                    if line['chipID']>0xFF:
                        print('ERROR: chipID too long or wrong IDType')

                    din = (line['chipID']<<1) | (line['command']<<9) | (line['payload']<<16) | line['IDType'] 
                    oline = oline + ',0x{:08X}'.format(din)
                    if 'mask' in line.keys():
                        oline = oline + ',0x{:04X}'.format(line['mask'])
                    else:
                        oline = oline + ','
                    if 'IDType' in line.keys():
                        oline = oline + ',{:1d}'.format(line['IDType'])
                    else:
                        oline = oline + ','
                    oline = oline + ',0x{:04X},0b{:07b},0x{:08X}'.format(line['chipID'], line['command'], line['payload'])
                else:
                    oline = oline + ',,,,,,'

                if 'comment' in line.keys():
                    oline = oline + ',' + line['comment']
                else:
                    oline = oline + ','


            oBuf_CSV.append(oline+'\n')

        with open(fname,'w+') as f:
            f.writelines(oBuf_CSV)

        return oBuf_CSV