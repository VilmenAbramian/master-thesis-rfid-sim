import unittest
from random import uniform
from pysim import epcstd


class TestDataTypes(unittest.TestCase):

    def test_divide_ratio_encoding(self):
        self.assertEqual(epcstd.DivideRatio.DR_8.code, "0")
        self.assertEqual(epcstd.DivideRatio.DR_643.code, "1")

    def test_divide_ratio_str(self):
        self.assertEqual(str(epcstd.DivideRatio.DR_8), '8')
        self.assertEqual(str(epcstd.DivideRatio.DR_643), '64/3')

    def test_divide_ratio_eval(self):
        self.assertAlmostEqual(epcstd.DivideRatio.DR_8.eval(), 8.0)
        self.assertAlmostEqual(epcstd.DivideRatio.DR_643.eval(), 64.0/3)

    def test_session_encoding(self):
        self.assertEqual(epcstd.Session.S0.code, "00")
        self.assertEqual(epcstd.Session.S1.code, "01")
        self.assertEqual(epcstd.Session.S2.code, "10")
        self.assertEqual(epcstd.Session.S3.code, "11")

    def test_session_number(self):
        self.assertEqual(epcstd.Session.S0.index, 0)
        self.assertEqual(epcstd.Session.S1.index, 1)
        self.assertEqual(epcstd.Session.S2.index, 2)
        self.assertEqual(epcstd.Session.S3.index, 3)

    def test_session_str(self):
        self.assertEqual(str(epcstd.Session.S0).upper(), "S0")
        self.assertEqual(str(epcstd.Session.S1).upper(), "S1")
        self.assertEqual(str(epcstd.Session.S2).upper(), "S2")
        self.assertEqual(str(epcstd.Session.S3).upper(), "S3")

    def test_tag_encoding_encoding(self):
        self.assertEqual(epcstd.TagEncoding.FM0.code, '00')
        self.assertEqual(epcstd.TagEncoding.M2.code, '01')
        self.assertEqual(epcstd.TagEncoding.M4.code, '10')
        self.assertEqual(epcstd.TagEncoding.M8.code, '11')

    def test_tag_encoding_symbols_per_bit(self):
        self.assertEqual(epcstd.TagEncoding.FM0.symbols_per_bit, 1)
        self.assertEqual(epcstd.TagEncoding.M2.symbols_per_bit, 2)
        self.assertEqual(epcstd.TagEncoding.M4.symbols_per_bit, 4)
        self.assertEqual(epcstd.TagEncoding.M8.symbols_per_bit, 8)

    def test_tag_encoding_str(self):
        self.assertEqual(str(epcstd.TagEncoding.FM0).upper(), "FM0")
        self.assertEqual(str(epcstd.TagEncoding.M2).upper(), "M2")
        self.assertEqual(str(epcstd.TagEncoding.M4).upper(), "M4")
        self.assertEqual(str(epcstd.TagEncoding.M8).upper(), "M8")

    def test_inventory_flag_encoding(self):
        self.assertEqual(epcstd.InventoryFlag.A.code, '0')
        self.assertEqual(epcstd.InventoryFlag.B.code, '1')

    def test_inventory_flag_str(self):
        self.assertEqual(str(epcstd.InventoryFlag.A).upper(), "A")
        self.assertEqual(str(epcstd.InventoryFlag.B).upper(), "B")

    def test_sel_flag_encoding(self):
        self.assertIn(epcstd.SelFlag.ALL.code, ['00', '01'])
        self.assertEqual(epcstd.SelFlag.NOT_SEL.code, '10')
        self.assertEqual(epcstd.SelFlag.SEL.code, '11')

    def test_sel_flag_str(self):
        self.assertEqual(str(epcstd.SelFlag.ALL).lower(), "all")
        self.assertEqual(str(epcstd.SelFlag.SEL).lower(), "sl")
        self.assertEqual(str(epcstd.SelFlag.NOT_SEL).lower(), "~sl")

    def test_memory_bank_encoding(self):
        self.assertEqual(epcstd.MemoryBank.RESERVED.code, '00')
        self.assertEqual(epcstd.MemoryBank.EPC.code, '01')
        self.assertEqual(epcstd.MemoryBank.TID.code, '10')
        self.assertEqual(epcstd.MemoryBank.USER.code, '11')

    def test_command_code_encoding(self):
        self.assertEqual(epcstd.CommandCode.QUERY.code, '1000')
        self.assertEqual(epcstd.CommandCode.QUERY_REP.code, '00')
        self.assertEqual(epcstd.CommandCode.ACK.code, '01')
        self.assertEqual(epcstd.CommandCode.REQ_RN.code, '11000001')
        self.assertEqual(epcstd.CommandCode.READ.code, '11000010')

    def test_command_code_str(self):
        self.assertEqual(str(epcstd.CommandCode.QUERY).lower(), "query")
        self.assertIn(str(epcstd.CommandCode.QUERY_REP).lower(),
                      ['query_rep', 'qrep', 'queryrep'])
        self.assertEqual(str(epcstd.CommandCode.ACK).lower(), 'ack')
        self.assertIn(str(epcstd.CommandCode.REQ_RN).lower(),
                      ['req_rn', 'reqrn'])
        self.assertEqual(str(epcstd.CommandCode.READ).lower(), 'read')


class TestEncodingFunctions(unittest.TestCase):

    def test_encode_bool(self):
        self.assertEqual(epcstd.encode_bool(True), '1')
        self.assertEqual(epcstd.encode_bool(False), '0')

    def test_encode_int(self):
        self.assertEqual(epcstd.encode_int(0, 4), '0000')
        self.assertEqual(epcstd.encode_int(0xF, 4), '1111')
        self.assertEqual(epcstd.encode_byte(0xA5), '10100101')
        self.assertEqual(epcstd.encode_word(0xAB3C), '1010101100111100')

    def test_ebv(self):
        self.assertEqual(epcstd.encode_ebv(0), '00000000')
        self.assertEqual(epcstd.encode_ebv(1), '00000001')
        self.assertEqual(epcstd.encode_ebv(127), '01111111')
        self.assertEqual(epcstd.encode_ebv(128), '1000000100000000')
        self.assertEqual(epcstd.encode_ebv(16383), '1111111101111111')
        self.assertEqual(epcstd.encode_ebv(16384), '100000011000000000000000')


class TestCommands(unittest.TestCase):

    def test_query_command_encoding(self):
        cmd1 = epcstd.Query(dr=epcstd.DivideRatio.DR_8,
                            m=epcstd.TagEncoding.FM0, trext=False,
                            sel=epcstd.SelFlag.ALL,
                            session=epcstd.Session.S0,
                            target=epcstd.InventoryFlag.A, q=0,
                            crc=0x00)
        self.assertEqual(cmd1.encode(), '1000000000000000000000')
        self.assertEqual(cmd1.bitlen, 22)
        cmd2 = epcstd.Query(dr=epcstd.DivideRatio.DR_643,
                            m=epcstd.TagEncoding.M8, trext=True,
                            sel=epcstd.SelFlag.SEL,
                            session=epcstd.Session.S3,
                            target=epcstd.InventoryFlag.B, q=6,
                            crc=0x0B)
        self.assertEqual(cmd2.encode(), '1000111111111011001011')

    def test_query_command_str(self):
        cmd = epcstd.Query(dr=epcstd.DivideRatio.DR_8,
                           m=epcstd.TagEncoding.FM0, trext=False,
                           sel=epcstd.SelFlag.ALL,
                           session=epcstd.Session.S0,
                           target=epcstd.InventoryFlag.A, q=13,
                           crc=0x1F)
        string = str(cmd)
        self.assertIn(str(epcstd.CommandCode.QUERY), string)
        self.assertIn(str(epcstd.DivideRatio.DR_8), string)
        self.assertIn(str(epcstd.TagEncoding.FM0), string)
        self.assertIn(str(epcstd.SelFlag.ALL), string)
        self.assertIn(str(epcstd.Session.S0), string)
        self.assertIn(str(epcstd.InventoryFlag.A), string)
        self.assertIn("13", string)
        self.assertIn("1F", string)

    def test_query_command_using_modelParams(self):
        #
        # 1) Setting some initial values for Query fields in readerParams
        #    and making sure they are passed to Query as default values
        #
        epcstd.stdParams.divide_ratio = epcstd.DivideRatio.DR_8
        epcstd.stdParams.tag_encoding = epcstd.TagEncoding.FM0
        epcstd.stdParams.sel = epcstd.SelFlag.SEL
        epcstd.stdParams.session = epcstd.Session.S0
        epcstd.stdParams.target = epcstd.InventoryFlag.A
        epcstd.stdParams.Q = 3
        epcstd.stdParams.trext = False

        query1 = epcstd.Query()

        def assert_query_params(query):
            self.assertEqual(query.dr, epcstd.stdParams.divide_ratio)
            self.assertEqual(query.m, epcstd.stdParams.tag_encoding)
            self.assertEqual(query.sel, epcstd.stdParams.sel)
            self.assertEqual(query.session, epcstd.stdParams.session)
            self.assertEqual(query.target, epcstd.stdParams.target)
            self.assertEqual(query.q, epcstd.stdParams.Q)
            self.assertEqual(query.trext, epcstd.stdParams.trext)

        assert_query_params(query1)

        #
        # 2) Altering values in readerParams and making sure they are
        #    passed to Query
        #
        epcstd.stdParams.divide_ratio = epcstd.DivideRatio.DR_643
        epcstd.stdParams.tag_encoding = epcstd.TagEncoding.M8
        epcstd.stdParams.sel = epcstd.SelFlag.NOT_SEL
        epcstd.stdParams.session = epcstd.Session.S3
        epcstd.stdParams.target = epcstd.InventoryFlag.B
        epcstd.stdParams.Q = 8
        epcstd.stdParams.trext = True

        query2 = epcstd.Query()

        assert_query_params(query2)

    def test_query_rep_command_encoding(self):
        cmd1 = epcstd.QueryRep(session=epcstd.Session.S0)
        self.assertEqual(cmd1.encode(), '0000')
        self.assertEqual(cmd1.bitlen, 4)
        cmd2 = epcstd.QueryRep(session=epcstd.Session.S3)
        self.assertEqual(cmd2.encode(), '0011')

    def test_query_rep_command_str(self):
        cmd = epcstd.QueryRep(session=epcstd.Session.S1)
        string = str(cmd)
        self.assertIn(str(epcstd.CommandCode.QUERY_REP), string)
        self.assertIn(str(epcstd.Session.S1), string)

    def test_query_rep_using_modelparams(self):
        def assert_fields_match_reader_params(query_rep):
            self.assertEqual(query_rep.session, epcstd.stdParams.session)

        # 1) Setting readerParams and checking they were passed to the
        #    command as the default params
        epcstd.stdParams.session = epcstd.Session.S0
        query_rep_1 = epcstd.QueryRep()
        assert_fields_match_reader_params(query_rep_1)

        # 2) Changing readerParams and checking the changed
        #    values were passed to new command as the default params
        epcstd.stdParams.session = epcstd.Session.S3
        query_rep_2 = epcstd.QueryRep()
        assert_fields_match_reader_params(query_rep_2)

    def test_ack_command_encoding(self):
        cmd1 = epcstd.Ack(rn=0x0000)
        self.assertEqual(cmd1.encode(), '010000000000000000')
        self.assertEqual(cmd1.bitlen, 18)
        cmd2 = epcstd.Ack(rn=0xFFFF)
        self.assertEqual(cmd2.encode(), '011111111111111111')

    def test_ack_command_str(self):
        cmd = epcstd.Ack(rn=0xAB)
        string = str(cmd)
        self.assertIn(str(epcstd.CommandCode.ACK), string)
        self.assertIn('0x00AB', string)

    def test_req_rn_command_encoding(self):
        cmd1 = epcstd.ReqRN(rn=0x0000, crc=0x0000)
        cmd2 = epcstd.ReqRN(rn=0xAAAA, crc=0x5555)
        self.assertEqual(cmd1.encode(),
                         '1100000100000000000000000000000000000000')
        self.assertEqual(cmd1.bitlen, 40)
        self.assertEqual(cmd2.encode(),
                         '1100000110101010101010100101010101010101')

    def test_req_rn_command_str(self):
        cmd1 = epcstd.ReqRN(rn=0x1234, crc=0xABCD)
        cmd2 = epcstd.ReqRN(rn=0xAABB, crc=0xCCDD)
        string1 = str(cmd1)
        string2 = str(cmd2)
        self.assertIn('0x1234', string1)
        self.assertIn('0xABCD', string1)
        self.assertIn('0xAABB', string2)
        self.assertIn('0xCCDD', string2)

    def test_read_command_encoding(self):
        cmd1 = epcstd.Read(bank=epcstd.MemoryBank.RESERVED, word_ptr=0,
                           word_count=0, rn=0x0000, crc=0x0000)
        cmd2 = epcstd.Read(bank=epcstd.MemoryBank.USER, word_ptr=0x80,
                           word_count=255, rn=0xAAAA, crc=0x5555)
        self.assertEqual(cmd1.encode(), '11000010' + '0' * 50)
        self.assertEqual(cmd1.bitlen, 58)
        self.assertEqual(cmd2.encode(), '11000010' + '11' + '1000000100000000'
                         + '1' * 8 + '1010' * 4 + '0101' * 4)

    def test_read_using_modelParams(self):
        def assert_fields_match_reader_params(cmd):
            assert isinstance(cmd, epcstd.Read)
            self.assertEqual(cmd.bank, epcstd.stdParams.read_default_bank)
            self.assertEqual(cmd.word_ptr,
                             epcstd.stdParams.read_default_word_ptr)
            self.assertEqual(cmd.word_count,
                             epcstd.stdParams.read_default_word_count)

        # 1) Setting readerParams and checking they were passed to the
        #    command as the default params
        epcstd.stdParams.read_default_bank = epcstd.MemoryBank.EPC
        epcstd.stdParams.read_default_word_ptr = 0
        epcstd.stdParams.read_default_word_count = 10
        cmd1 = epcstd.Read()
        assert_fields_match_reader_params(cmd1)

        # 2) Changing readerParams and checking the changed
        #    values were passed to new command as the default params
        epcstd.stdParams.read_default_bank = epcstd.MemoryBank.TID
        epcstd.stdParams.read_default_word_ptr = 5
        epcstd.stdParams.read_default_word_count = 23
        cmd2 = epcstd.Read()
        assert_fields_match_reader_params(cmd2)

    def test_read_command_str(self):
        cmd1 = epcstd.Read(bank=epcstd.MemoryBank.EPC, word_ptr=2,
                           word_count=5, rn=0xAABB, crc=0xCCDD)
        cmd2 = epcstd.Read(bank=epcstd.MemoryBank.TID, word_ptr=3,
                           word_count=1, rn=0xABCD, crc=0xEFEF)
        string1 = str(cmd1)
        string2 = str(cmd2)
        self.assertIn('EPC', string1.upper())
        self.assertIn('0x02', string1)
        self.assertIn('5', string1)
        self.assertIn('0xAABB', string1)
        self.assertIn('0xCCDD', string1)
        self.assertIn('TID', string2.upper())
        self.assertIn('0x03', string2)
        self.assertIn('1', string2)
        self.assertIn('0xABCD', string2)
        self.assertIn('0xEFEF', string2)


class TestReplies(unittest.TestCase):
    def test_to_bytes(self):
        self.assertEqual(epcstd.to_bytes('1122'), [0x11, 0x22])
        self.assertEqual(epcstd.to_bytes((0xAB,)), [0xAB])
        with self.assertRaises(ValueError):
            epcstd.to_bytes(0xAB)

    def test_query_reply_bitlen(self):
        msg = epcstd.QueryReply(rn=0x0000)
        self.assertEqual(msg.bitlen, 16)

    def test_query_reply_str(self):
        msg1 = epcstd.QueryReply(rn=0xABCD)
        msg2 = epcstd.QueryReply(rn=0x1122)
        string1 = str(msg1)
        string2 = str(msg2)
        self.assertIn('ABCD', string1.upper())
        self.assertNotIn('1122', string1)
        self.assertIn('1122', string2)
        self.assertNotIn('ABCD', string2.upper())

    def test_ack_reply_bitlen(self):
        msg1 = epcstd.AckReply(pc=0x0000, epc='0011223344556677', crc=0x0000)
        msg2 = epcstd.AckReply(pc=0x0000, epc='001122334455', crc=0x0000)
        msg3 = epcstd.AckReply(pc=0x0000, epc=[0x00, 0x11, 0x22], crc=0x0000)
        self.assertEqual(msg1.bitlen, 96)
        self.assertEqual(msg2.bitlen, 80)
        self.assertEqual(msg3.bitlen, 56)

    def test_ack_reply_str(self):
        msg1 = epcstd.AckReply(pc=0xABCD, epc='0011223344556677', crc=0x1234)
        msg2 = epcstd.AckReply(pc=0xDCBA, epc='001122334455', crc=0x4321)
        s1 = str(msg1)
        s2 = str(msg2)
        self.assertIn('ABCD', s1.upper())
        self.assertNotIn('DCBA', s1.upper())
        self.assertIn('1234', s1)
        self.assertNotIn('4321', s1)
        self.assertIn('0011223344556677', s1)
        self.assertIn('DCBA', s2.upper())
        self.assertIn('4321', s2)
        self.assertIn('001122334455', s2)
        self.assertNotIn('6677', s2)

    def test_req_rn_reply_bitlen(self):
        msg = epcstd.ReqRnReply(rn=0x0000, crc=0x0000)
        self.assertEqual(msg.bitlen, 32)

    def test_req_rn_reply_str(self):
        msg1 = epcstd.ReqRnReply(rn=0xABCD, crc=0x1234)
        msg2 = epcstd.ReqRnReply(rn=0xDCBA, crc=0x4321)
        s1 = str(msg1)
        s2 = str(msg2)
        self.assertIn('ABCD', s1.upper())
        self.assertIn('1234', s1)
        self.assertNotIn('DCBA', s1.upper())
        self.assertNotIn('4321', s1)
        self.assertIn('DCBA', s2.upper())
        self.assertIn('4321', s2)

    def test_read_reply_bitlen(self):
        msg1 = epcstd.ReadReply(data='00112233', rn=0x0000, crc=0x0000)
        msg2 = epcstd.ReadReply(data='001122334455', rn=0x0000, crc=0x0000)
        msg3 = epcstd.ReadReply(data=[0x00, 0x11], rn=0x0000, crc=0x0000)
        self.assertEqual(msg1.bitlen, 65)
        self.assertEqual(msg2.bitlen, 81)
        self.assertEqual(msg3.bitlen, 49)

    def test_read_reply_str(self):
        msg1 = epcstd.ReadReply(data='00112233', rn=0x1234, crc=0xABCD)
        msg2 = epcstd.ReadReply(data='AABBCC', rn=0x4321, crc=0xDCBA)
        s1 = str(msg1)
        s2 = str(msg2)
        self.assertIn('00112233', s1)
        self.assertIn('1234', s1)
        self.assertIn('ABCD', s1.upper())
        self.assertNotIn('AABBCC', s1.upper())
        self.assertNotIn('4321', s1)
        self.assertNotIn('DCBA', s1)
        self.assertIn('AABBCC', s2.upper())
        self.assertIn('4321', s2)
        self.assertIn('DCBA', s2.upper())


class TestReaderPreambles(unittest.TestCase):
    def test_reader_preamble_durations(self):
        p = epcstd.ReaderPreamble(tari=6.25e-6, rtcal=18.75e-6, trcal=56.25e-6)
        self.assertAlmostEqual(p.data0, p.tari, 9)
        self.assertAlmostEqual(p.delim, 12.5e-6, 9)
        self.assertAlmostEqual(p.data0, 6.25e-6, 9)
        self.assertAlmostEqual(p.data1, 12.5e-6, 9)
        self.assertAlmostEqual(p.rtcal, 18.75e-6, 9)
        self.assertAlmostEqual(p.trcal, 56.25e-6, 9)
        self.assertAlmostEqual(p.duration, 93.75e-6, 9)

    def test_reader_preamble_str(self):
        p = epcstd.ReaderPreamble(tari=12.5e-6, rtcal=33.45e-6, trcal=60.15e-6,
                                  delim=13.0e-6)
        s = str(p)
        self.assertIn("12.5", s)
        self.assertIn("33.45", s)
        self.assertIn("60.15", s)
        self.assertIn("13.0", s)

    def test_reader_sync_durations(self):
        sync = epcstd.ReaderSync(tari=12.5e-6, rtcal=31.25e-6, delim=13.0e-6)
        self.assertAlmostEqual(sync.tari, sync.data0, 9)
        self.assertAlmostEqual(sync.data0, 12.5e-6, 9)
        self.assertAlmostEqual(sync.data1, 18.75e-6, 9)
        self.assertAlmostEqual(sync.rtcal, 31.25e-6, 9)
        self.assertAlmostEqual(sync.delim, 13.0e-6)
        self.assertAlmostEqual(sync.duration, 56.75e-6, 9)

    def test_reader_sync_str(self):
        sync = epcstd.ReaderSync(tari=25e-6, rtcal=75e-6, delim=12.0e-6)
        s = str(sync)
        self.assertIn("12.0", s)
        self.assertIn("25.0", s)
        self.assertIn("75.0", s)


class TestTagPreambles(unittest.TestCase):
    def test_tag_FM0_preamble_bitlen_and_duration(self):
        short_preamble = epcstd.FM0Preamble(extended=False)
        long_preamble = epcstd.FM0Preamble(extended=True)
        self.assertEqual(short_preamble.bitlen, 6)
        self.assertEqual(long_preamble.bitlen, 18)
        self.assertAlmostEqual(short_preamble.get_duration(blf=320e3),
                               1.875e-5)
        self.assertAlmostEqual(long_preamble.get_duration(blf=320e3),
                               5.625e-5)
        self.assertAlmostEqual(short_preamble.get_duration(blf=40e3), 15e-5)
        self.assertAlmostEqual(long_preamble.get_duration(blf=40e3), 45e-5)

    def test_tag_miller_preamble_bitlen_and_duration(self):
        m2_short = epcstd.MillerPreamble(m=2, extended=False)
        m2_long = epcstd.MillerPreamble(m=2, extended=True)
        m4_short = epcstd.MillerPreamble(m=4)
        m8_long = epcstd.MillerPreamble(m=8, extended=True)
        self.assertEqual(m2_short.bitlen, 10)
        self.assertEqual(m2_long.bitlen, 22)
        self.assertEqual(m4_short.bitlen, 10)
        self.assertEqual(m8_long.bitlen, 22)
        self.assertAlmostEqual(m2_short.get_duration(blf=320e3), 6.25e-5)
        self.assertAlmostEqual(m2_long.get_duration(blf=320e3), 13.75e-5)
        self.assertAlmostEqual(m4_short.get_duration(blf=320e3), 12.5e-5)
        self.assertAlmostEqual(m8_long.get_duration(blf=320e3), 55e-5)
        self.assertAlmostEqual(m2_short.get_duration(blf=64e3), 31.25e-5)

    def test_tag_preamble_factory(self):
        fm0_preamble = epcstd.create_tag_preamble(epcstd.TagEncoding.FM0)
        fm0_extended_preamble = epcstd.create_tag_preamble(
            epcstd.TagEncoding.FM0, True)
        m2_preamble = epcstd.create_tag_preamble(epcstd.TagEncoding.M2)
        m4_preamble = epcstd.create_tag_preamble(epcstd.TagEncoding.M2)
        m8_preamble = epcstd.create_tag_preamble(epcstd.TagEncoding.M2)

        self.assertIsInstance(fm0_preamble, epcstd.FM0Preamble)
        self.assertIsInstance(fm0_extended_preamble, epcstd.FM0Preamble)
        self.assertIsInstance(m2_preamble, epcstd.MillerPreamble)
        self.assertIsInstance(m4_preamble, epcstd.MillerPreamble)
        self.assertIsInstance(m8_preamble, epcstd.MillerPreamble)
        self.assertEqual(fm0_preamble.bitlen, 6)
        self.assertEqual(fm0_extended_preamble.bitlen, 18)

    def test_tag_preamble_has_str(self):
        s1 = str(epcstd.FM0Preamble(True))
        s2 = str(epcstd.MillerPreamble(2, True))
        self.assertNotIn("0x", s1)
        self.assertNotIn("0x", s2)

    def test_tag_preamble_bitlen(self):
        epcstd.stdParams.trext = False
        fm0_normal = epcstd.create_tag_preamble(epcstd.TagEncoding.FM0, False)
        fm0_extended = epcstd.create_tag_preamble(epcstd.TagEncoding.FM0, True)
        m2_normal = epcstd.create_tag_preamble(epcstd.TagEncoding.M2, False)
        m2_extended = epcstd.create_tag_preamble(epcstd.TagEncoding.M2, True)

        self.assertEqual(fm0_normal.bitlen, epcstd.tag_preamble_bitlen(
            epcstd.TagEncoding.FM0))
        self.assertEqual(fm0_extended.bitlen, epcstd.tag_preamble_bitlen(
            epcstd.TagEncoding.FM0, True))
        self.assertEqual(m2_normal.bitlen, epcstd.tag_preamble_bitlen(
            epcstd.TagEncoding.M2))
        self.assertEqual(m2_extended.bitlen, epcstd.tag_preamble_bitlen(
            epcstd.TagEncoding.M2, True))

    def test_tag_preamble_duration(self):
        fm0_normal = epcstd.create_tag_preamble(epcstd.TagEncoding.FM0, False)
        fm0_extended = epcstd.create_tag_preamble(epcstd.TagEncoding.FM0, True)
        m2_normal = epcstd.create_tag_preamble(epcstd.TagEncoding.M2, False)
        m2_extended = epcstd.create_tag_preamble(epcstd.TagEncoding.M2, True)

        blf_slow = epcstd.get_blf(epcstd.DivideRatio.DR_8, 25.0e-6*9)
        blf_fast = epcstd.get_blf(epcstd.DivideRatio.DR_643, 6.25e-6 * 9)

        self.assertEqual(
            fm0_normal.get_duration(blf_slow), epcstd.tag_preamble_duration(
                blf_slow, epcstd.TagEncoding.FM0, False))
        self.assertEqual(
            fm0_normal.get_duration(blf_fast), epcstd.tag_preamble_duration(
                blf_fast, epcstd.TagEncoding.FM0, False))
        self.assertEqual(
            fm0_extended.get_duration(blf_slow), epcstd.tag_preamble_duration(
                blf_slow, epcstd.TagEncoding.FM0, True))
        self.assertEqual(
            fm0_extended.get_duration(blf_fast), epcstd.tag_preamble_duration(
                blf_fast, epcstd.TagEncoding.FM0, True))

        self.assertEqual(
            m2_normal.get_duration(blf_slow), epcstd.tag_preamble_duration(
                blf_slow, epcstd.TagEncoding.M2, False))
        self.assertEqual(
            m2_normal.get_duration(blf_fast), epcstd.tag_preamble_duration(
                blf_fast, epcstd.TagEncoding.M2, False))
        self.assertEqual(
            m2_extended.get_duration(blf_slow), epcstd.tag_preamble_duration(
                blf_slow, epcstd.TagEncoding.M2, True))
        self.assertEqual(
            m2_extended.get_duration(blf_fast), epcstd.tag_preamble_duration(
                blf_fast, epcstd.TagEncoding.M2, True))


class TestReaderFrames(unittest.TestCase):
    def setUp(self):
        # The following query will be encoded as 1000011011010001101010
        # number of 1s: 10, number of 0s: 12
        self.query = epcstd.Query(
            dr=epcstd.DivideRatio.DR_8, m=epcstd.TagEncoding.M8, trext=False,
            sel=epcstd.SelFlag.SEL, session=epcstd.Session.S1,
            target=epcstd.InventoryFlag.A, q=3, crc=0xAA)

        # The following QueryRep will be encoded as 0011
        self.query_rep = epcstd.QueryRep(session=epcstd.Session.S3)

        # Now we define a fast preamble, a slow preamble and a SYNC:
        self.fast_preamble = epcstd.ReaderPreamble(
            tari=6.25e-6, rtcal=18.75e-6, trcal=56.25e-6)
        self.slow_preamble = epcstd.ReaderPreamble(
            tari=25e-6, rtcal=75e-6, trcal=225e-6)
        self.fast_sync = epcstd.ReaderSync(tari=12.5e-6, rtcal=31.25e-6)
        self.slow_sync = epcstd.ReaderSync(tari=25e-6, rtcal=62.5e-6)

    def test_query_frame_fast_preamble_duration(self):
        f = epcstd.ReaderFrame(preamble=self.fast_preamble, command=self.query)
        self.assertAlmostEqual(f.duration, 293.75e-6, 9)
        self.assertAlmostEqual(f.body_duration, 200e-6, 9)

    def test_query_frame_slow_preamble_duration(self):
        f = epcstd.ReaderFrame(preamble=self.slow_preamble, command=self.query)
        self.assertAlmostEqual(f.duration, 1137.5e-6, 9)
        self.assertAlmostEqual(f.body_duration, 800.0e-6, 9)

    def test_query_rep_frame_fast_sync_duration(self):
        f = epcstd.ReaderFrame(preamble=self.fast_sync, command=self.query_rep)
        self.assertAlmostEqual(f.body_duration, 62.5e-6, 9)
        self.assertAlmostEqual(f.duration, 118.75e-6, 9)

    def test_query_rep_frame_slow_sync_duration(self):
        f = epcstd.ReaderFrame(preamble=self.slow_sync, command=self.query_rep)
        self.assertAlmostEqual(f.body_duration, 125e-6, 9)
        self.assertAlmostEqual(f.duration, 225e-6, 9)


class TestTagFrames(unittest.TestCase):
    def setUp(self):
        self.ack_reply = epcstd.AckReply(epc="ABCDEF01", pc=0, crc=0)
        self.rn16_reply = epcstd.QueryReply(rn=0)
        self.slow_blf = 120e3
        self.fast_blf = 640e3

    def test_tag_fm0_frame_duration(self):
        pn = epcstd.create_tag_preamble(epcstd.TagEncoding.FM0, extended=False)
        pe = epcstd.create_tag_preamble(epcstd.TagEncoding.FM0, extended=True)

        ne_ack_frame = epcstd.TagFrame(preamble=pn, reply=self.ack_reply)
        ex_ack_frame = epcstd.TagFrame(preamble=pe, reply=self.ack_reply)
        ex_rn16_frame = epcstd.TagFrame(preamble=pe, reply=self.rn16_reply)

        self.assertAlmostEqual(ne_ack_frame.get_body_duration(self.slow_blf),
                               0.00053333333, 8)
        self.assertAlmostEqual(ne_ack_frame.get_duration(self.slow_blf),
                               0.00059166667, 8)
        self.assertAlmostEqual(ex_ack_frame.get_body_duration(self.slow_blf),
                               0.00053333333, 8)
        self.assertAlmostEqual(ex_ack_frame.get_duration(self.slow_blf),
                               0.00069166667, 8)
        self.assertAlmostEqual(ex_rn16_frame.get_body_duration(self.slow_blf),
                               0.00013333333, 8)
        self.assertAlmostEqual(ex_rn16_frame.get_duration(self.slow_blf),
                               0.00029166667, 8)
        self.assertAlmostEqual(ex_rn16_frame.get_body_duration(self.fast_blf),
                               2.5e-05, 8)
        self.assertAlmostEqual(ex_rn16_frame.get_duration(self.fast_blf),
                               5.46875e-05)

    def test_tag_m2_frame_duration(self):
        preamble = epcstd.create_tag_preamble(epcstd.TagEncoding.M2, False)
        ext_preamble = epcstd.create_tag_preamble(epcstd.TagEncoding.M2, True)

        frame = epcstd.TagFrame(preamble, self.rn16_reply)
        ext_frame = epcstd.TagFrame(ext_preamble, self.rn16_reply)

        self.assertAlmostEqual(frame.get_body_duration(self.slow_blf),
                               0.0002666666666666667, 8)
        self.assertAlmostEqual(frame.get_duration(self.slow_blf),
                               0.00045, 8)
        self.assertAlmostEqual(frame.get_body_duration(self.fast_blf),
                               5e-05, 8)
        self.assertAlmostEqual(frame.get_duration(self.fast_blf),
                               8.4375e-05, 8)
        self.assertAlmostEqual(ext_frame.get_body_duration(self.slow_blf),
                               frame.get_body_duration(self.slow_blf), 8)
        self.assertAlmostEqual(ext_frame.get_duration(self.slow_blf),
                               0.00065, 8)


class TestReaderFrameAccessors(unittest.TestCase):

    def setUp(self):
        self.slow_tari = 12.5e-6
        self.slow_rtcal = 37.5e-6
        self.slow_trcal = 112.5e-6
        self.fast_tari = 6.25e-6
        self.fast_rtcal = 15.625e-6
        self.fast_trcal = 46.875e-6

        self.slow_sync = epcstd.ReaderSync(self.slow_tari, self.slow_rtcal)
        self.fast_sync = epcstd.ReaderSync(self.fast_tari, self.fast_rtcal)
        self.slow_preamble = epcstd.ReaderPreamble(
            self.slow_tari, self.slow_rtcal, self.slow_trcal)
        self.fast_preamble = epcstd.ReaderPreamble(
            self.fast_tari, self.fast_rtcal, self.fast_trcal)

        self.ack = epcstd.Ack(0xAAAA)
        self.query_rep = epcstd.QueryRep(epcstd.Session.S1)
        self.query = epcstd.Query()

        self.slow_ack_frame = epcstd.ReaderFrame(self.slow_sync, self.ack)
        self.fast_ack_frame = epcstd.ReaderFrame(self.fast_sync, self.ack)
        self.slow_query_rep_frame = epcstd.ReaderFrame(
            self.slow_sync, self.query_rep)
        self.fast_query_rep_frame = epcstd.ReaderFrame(
            self.fast_sync, self.query_rep)
        self.slow_query_frame = epcstd.ReaderFrame(
            self.slow_preamble, self.query)
        self.fast_query_frame = epcstd.ReaderFrame(
            self.fast_preamble, self.query)

    def test_reader_frame_duration_return_equals_sync_frame_getter(self):
        self.assertAlmostEqual(
            epcstd.reader_frame_duration(
                tari=self.slow_tari, rtcal=self.slow_rtcal, command=self.ack),
            self.slow_ack_frame.duration, 8)
        self.assertAlmostEqual(
            epcstd.reader_frame_duration(
                tari=self.fast_tari, rtcal=self.fast_rtcal, command=self.ack),
            self.fast_ack_frame.duration, 8)
        self.assertAlmostEqual(
            epcstd.reader_frame_duration(
                tari=self.slow_tari, rtcal=self.slow_rtcal,
                command=self.query_rep),
            self.slow_query_rep_frame.duration, 8)
        self.assertAlmostEqual(
            epcstd.reader_frame_duration(
                tari=self.fast_tari, rtcal=self.fast_rtcal,
                command=self.query_rep),
            self.fast_query_rep_frame.duration, 8)

    def test_reader_frame_duration_return_equals_query_frame_getter(self):
        self.assertAlmostEqual(
            epcstd.reader_frame_duration(
                tari=self.slow_tari, rtcal=self.slow_rtcal,
                trcal=self.slow_trcal, command=self.query),
            self.slow_query_frame.duration, 8)
        self.assertAlmostEqual(
            epcstd.reader_frame_duration(
                tari=self.fast_tari, rtcal=self.fast_rtcal,
                trcal=self.fast_trcal, command=self.query),
            self.fast_query_frame.duration, 8)

    def test_reader_frame_duration_recognizes_encoded_sync_commands(self):
        encoded_ack = self.ack.encode()
        encoded_query_rep = self.query_rep.encode()
        self.assertAlmostEqual(
            epcstd.reader_frame_duration(
                tari=self.slow_tari, rtcal=self.slow_rtcal,
                command=encoded_ack),
            self.slow_ack_frame.duration, 8)
        self.assertAlmostEqual(
            epcstd.reader_frame_duration(
                tari=self.fast_tari, rtcal=self.fast_rtcal,
                command=encoded_ack),
            self.fast_ack_frame.duration, 8)
        self.assertAlmostEqual(
            epcstd.reader_frame_duration(
                tari=self.slow_tari, rtcal=self.slow_rtcal,
                command=encoded_query_rep),
            self.slow_query_rep_frame.duration, 8)
        self.assertAlmostEqual(
            epcstd.reader_frame_duration(
                tari=self.fast_tari, rtcal=self.fast_rtcal,
                command=encoded_query_rep),
            self.fast_query_rep_frame.duration, 8)

    def test_reader_frame_duration_recognizes_encoded_query_command(self):
        encoded_query = self.query.encode()
        self.assertAlmostEqual(
            epcstd.reader_frame_duration(
                tari=self.slow_tari, rtcal=self.slow_rtcal,
                trcal=self.slow_trcal, command=encoded_query),
            self.slow_query_frame.duration, 8)
        self.assertAlmostEqual(
            epcstd.reader_frame_duration(
                tari=self.fast_tari, rtcal=self.fast_rtcal,
                trcal=self.fast_trcal, command=encoded_query),
            self.fast_query_frame.duration, 8)

    def test_reader_frame_duration_uses_default_modelParams(self):
        #
        # 1) Setting readerParams to slow frame type
        #
        epcstd.stdParams.tari = self.slow_tari
        epcstd.stdParams.rtcal = self.slow_rtcal
        epcstd.stdParams.trcal = self.slow_trcal
        self.assertAlmostEqual(
            epcstd.reader_frame_duration(self.ack),
            self.slow_ack_frame.duration, 8)
        self.assertAlmostEqual(
            epcstd.reader_frame_duration(self.query_rep),
            self.slow_query_rep_frame.duration, 8)
        self.assertAlmostEqual(
            epcstd.reader_frame_duration(self.query),
            self.slow_query_frame.duration, 8)

        #
        # 1) Setting readerParams to fast frame type
        #
        epcstd.stdParams.tari = self.fast_tari
        epcstd.stdParams.rtcal = self.fast_rtcal
        epcstd.stdParams.trcal = self.fast_trcal
        self.assertAlmostEqual(
            epcstd.reader_frame_duration(self.ack),
            self.fast_ack_frame.duration, 8)
        self.assertAlmostEqual(
            epcstd.reader_frame_duration(self.query_rep),
            self.fast_query_rep_frame.duration, 8)
        self.assertAlmostEqual(
            epcstd.reader_frame_duration(self.query),
            self.fast_query_frame.duration, 8)


class TestCommandsDurationEstimations(unittest.TestCase):
    """
    Test-cases for functions ``command_duration``, ``query_duration``,
    ``query_rep_duration``, etc.
    """
    def setUp(self):
        self.slow = dict(
            tari=25.0e-6, rtcal=75.0e-6, trcal=225.0e-6, delim=12.5e-6,
            dr=epcstd.DivideRatio.DR_8, m=epcstd.TagEncoding.M8, trext=True,
            sel=epcstd.SelFlag.SEL, session=epcstd.Session.S3,
            target=epcstd.InventoryFlag.B, q=15, rn=0xFFFF,
            bank=epcstd.MemoryBank.TID, word_ptr=0xF, word_cnt=15,
            crc5=0x1F, crc16=0xFFFF)

        self.fast = dict(
            tari=6.25e-6, rtcal=15.625e-6, trcal=17.1875e-6, delim=12.5e-6,
            dr=epcstd.DivideRatio.DR_643, m=epcstd.TagEncoding.FM0, trext=False,
            sel=epcstd.SelFlag.ALL, session=epcstd.Session.S0,
            target=epcstd.InventoryFlag.A, q=0, rn=0x0000,
            bank=epcstd.MemoryBank.EPC, word_ptr=0x0, word_cnt=1,
            crc5=0x00, crc16=0x0000)

        self.slow['preamble'] = epcstd.ReaderPreamble(
            self.slow['tari'], self.slow['rtcal'], self.slow['trcal'],
            self.slow['delim'])
        self.fast['preamble'] = epcstd.ReaderPreamble(
            self.fast['tari'], self.fast['rtcal'], self.fast['trcal'],
            self.fast['delim'])
        self.slow['sync'] = epcstd.ReaderSync(
            self.slow['tari'], self.slow['rtcal'], self.slow['delim'])
        self.fast['sync'] = epcstd.ReaderSync(
            self.fast['tari'], self.fast['rtcal'], self.fast['delim'])

    @staticmethod
    def get_command_duration(command_code, params):
        return epcstd.command_duration(
            command_code=command_code, tari=params['tari'],
            rtcal=params['rtcal'], trcal=params['trcal'], delim=params['delim'],
            dr=params['dr'], m=params['m'], trext=params['trext'],
            sel=params['sel'], session=params['session'],
            target=params['target'], q=params['q'], rn=params['rn'],
            bank=params['bank'], word_ptr=params['word_ptr'],
            word_count=params['word_cnt'], crc5=params['crc5'],
            crc16=params['crc16'])

    @staticmethod
    def set_default_parameters(par):
        epcstd.stdParams.tari = par['tari']
        epcstd.stdParams.rtcal = par['rtcal']
        epcstd.stdParams.trcal = par['trcal']
        epcstd.stdParams.delim = par['delim']
        epcstd.stdParams.divide_ratio = par['dr']
        epcstd.stdParams.tag_encoding = par['m']
        epcstd.stdParams.trext = par['trext']
        epcstd.stdParams.sel = par['sel']
        epcstd.stdParams.session = par['session']
        epcstd.stdParams.target = par['target']
        epcstd.stdParams.Q = par['q']
        epcstd.stdParams.default_rn = par['rn']
        epcstd.stdParams.read_default_bank = par['bank']
        epcstd.stdParams.read_default_word_ptr = par['word_ptr']
        epcstd.stdParams.read_default_word_count = par['word_cnt']
        epcstd.stdParams.default_crc5 = par['crc5']
        epcstd.stdParams.default_crc16 = par['crc16']

    def test_query_duration(self):
        slow_query = epcstd.Query(
            self.slow['dr'], self.slow['m'], self.slow['trext'],
            self.slow['sel'], self.slow['session'], self.slow['target'],
            self.slow['q'], self.slow['crc5'])
        fast_query = epcstd.Query(
            self.fast['dr'], self.fast['m'], self.fast['trext'],
            self.fast['sel'], self.fast['session'], self.fast['target'],
            self.fast['q'], self.fast['crc5'])
        slow_frame = epcstd.ReaderFrame(self.slow['preamble'], slow_query)
        fast_frame = epcstd.ReaderFrame(self.fast['preamble'], fast_query)

        self.assertAlmostEqual(
            slow_frame.duration,
            self.get_command_duration(epcstd.CommandCode.QUERY, self.slow),
            8, "command_duration(QUERY, slow) doesn't match frame")
        self.assertAlmostEqual(
            slow_frame.duration,
            epcstd.query_duration(
                tari=self.slow['tari'], rtcal=self.slow['rtcal'],
                trcal=self.slow['trcal'], delim=self.slow['delim'],
                dr=self.slow['dr'], m=self.slow['m'], trext=self.slow['trext'],
                sel=self.slow['sel'], session=self.slow['session'],
                target=self.slow['target'], q=self.slow['q'],
                crc=self.slow['crc5']),
            8, "query_duration(slow params) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.duration,
            self.get_command_duration(epcstd.CommandCode.QUERY, self.fast),
            8, "command_duration(QUERY, fast) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.duration,
            epcstd.query_duration(
                tari=self.fast['tari'], rtcal=self.fast['rtcal'],
                trcal=self.fast['trcal'], delim=self.fast['delim'],
                dr=self.fast['dr'], m=self.fast['m'], trext=self.fast['trext'],
                sel=self.fast['sel'], session=self.fast['session'],
                target=self.fast['target'], q=self.fast['q'],
                crc=self.fast['crc5']),
            8, "query_duration(fast params) doesn't match frame")

    def test_query_duration_with_default_parameters(self):
        slow_query = epcstd.Query(
            self.slow['dr'], self.slow['m'], self.slow['trext'],
            self.slow['sel'], self.slow['session'], self.slow['target'],
            self.slow['q'], self.slow['crc5'])
        fast_query = epcstd.Query(
            self.fast['dr'], self.fast['m'], self.fast['trext'],
            self.fast['sel'], self.fast['session'], self.fast['target'],
            self.fast['q'], self.fast['crc5'])
        slow_frame = epcstd.ReaderFrame(self.slow['preamble'], slow_query)
        fast_frame = epcstd.ReaderFrame(self.fast['preamble'], fast_query)

        self.set_default_parameters(self.slow)

        self.assertAlmostEqual(
            slow_frame.duration,
            epcstd.command_duration(epcstd.CommandCode.QUERY), 8,
            "command_duration(QUERY, default=slow) doesn't match frame")
        self.assertAlmostEqual(
            slow_frame.duration,
            epcstd.query_duration(), 8,
            "query_duration(default=slow) doesnt' match frame")

        self.set_default_parameters(self.fast)

        self.assertAlmostEqual(
            fast_frame.duration,
            epcstd.command_duration(epcstd.CommandCode.QUERY), 8,
            "command_duration(QUERY, default=fast) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.duration,
            epcstd.query_duration(), 8,
            "query_duration(default=fast) doesn't match frame")

    def test_query_rep_duration(self):
        slow_qrep = epcstd.QueryRep(self.slow['session'])
        fast_qrep = epcstd.QueryRep(self.fast['session'])
        slow_frame = epcstd.ReaderFrame(self.slow['sync'], slow_qrep)
        fast_frame = epcstd.ReaderFrame(self.fast['sync'], fast_qrep)

        self.assertAlmostEqual(
            slow_frame.duration,
            self.get_command_duration(epcstd.CommandCode.QUERY_REP, self.slow),
            8, "command_duration(QUERY_REP, slow) doesn't match frame")
        self.assertAlmostEqual(
            slow_frame.duration,
            epcstd.query_rep_duration(
                tari=self.slow['tari'], rtcal=self.slow['rtcal'],
                trcal=self.slow['trcal'], delim=self.slow['delim'],
                session=self.slow['session']),
            8, "query_rep_duration(slow) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.duration,
            self.get_command_duration(epcstd.CommandCode.QUERY_REP, self.fast),
            8, "command_duration(QUERY_REP, fast) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.duration,
            epcstd.query_rep_duration(
                tari=self.fast['tari'], rtcal=self.fast['rtcal'],
                trcal=self.fast['trcal'], delim=self.fast['delim'],
                session=self.fast['session']),
            8, "query_rep_duration(fast) doesn't match frame")

    def test_query_rep_duration_with_default_parameters(self):
        slow_qrep = epcstd.QueryRep(self.slow['session'])
        fast_qrep = epcstd.QueryRep(self.fast['session'])
        slow_frame = epcstd.ReaderFrame(self.slow['sync'], slow_qrep)
        fast_frame = epcstd.ReaderFrame(self.fast['sync'], fast_qrep)

        self.set_default_parameters(self.slow)

        self.assertAlmostEqual(
            slow_frame.duration,
            epcstd.command_duration(epcstd.CommandCode.QUERY_REP), 8,
            "command_duration(QUERY_REP, default=slow) doesn't match frame")
        self.assertAlmostEqual(
            slow_frame.duration, epcstd.query_rep_duration(), 8,
            "query_rep_duration(default=slow) doesn't match frame")

        self.set_default_parameters(self.fast)

        self.assertAlmostEqual(
            fast_frame.duration,
            epcstd.command_duration(epcstd.CommandCode.QUERY_REP), 8,
            "command_duration(QUERY_REP, default=fast) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.duration, epcstd.query_rep_duration(), 8,
            "query_rep_duration(default=fast) doesn't match frame")

    def test_ack_duration(self):
        slow_ack = epcstd.Ack(self.slow['rn'])
        fast_ack = epcstd.Ack(self.fast['rn'])
        slow_frame = epcstd.ReaderFrame(self.slow['sync'], slow_ack)
        fast_frame = epcstd.ReaderFrame(self.fast['sync'], fast_ack)

        self.assertAlmostEqual(
            slow_frame.duration,
            self.get_command_duration(epcstd.CommandCode.ACK, self.slow),
            8, "command_duration(ACK, slow) doesn't match frame")
        self.assertAlmostEqual(
            slow_frame.duration,
            epcstd.ack_duration(
                tari=self.slow['tari'], rtcal=self.slow['rtcal'],
                trcal=self.slow['trcal'], delim=self.slow['delim'],
                rn=self.slow['rn']),
            8, "ack_duration(slow) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.duration,
            self.get_command_duration(epcstd.CommandCode.ACK, self.fast),
            8, "command_duration(ACK, fast) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.duration,
            epcstd.ack_duration(
                tari=self.fast['tari'], rtcal=self.fast['rtcal'],
                trcal=self.fast['trcal'], delim=self.fast['delim'],
                rn=self.fast['rn']),
            8, "ack_duration(fast) doesn't match frame")

    def test_ack_duration_with_default_parameters(self):
        slow_ack = epcstd.Ack(self.slow['rn'])
        fast_ack = epcstd.Ack(self.fast['rn'])
        slow_frame = epcstd.ReaderFrame(self.slow['sync'], slow_ack)
        fast_frame = epcstd.ReaderFrame(self.fast['sync'], fast_ack)

        self.set_default_parameters(self.slow)

        self.assertAlmostEqual(
            slow_frame.duration,
            epcstd.command_duration(epcstd.CommandCode.ACK), 8,
            "command_duration(ACK, default=slow) doesn't match frame")
        self.assertAlmostEqual(
            slow_frame.duration, epcstd.ack_duration(), 8,
            "ack_duration(default=slow) doesn't match frame")

        self.set_default_parameters(self.fast)

        self.assertAlmostEqual(
            fast_frame.duration,
            epcstd.command_duration(epcstd.CommandCode.ACK), 8,
            "command_duration(ACK, default=fast) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.duration, epcstd.ack_duration(), 8,
            "ack_duration(default=fast) doesn't match frame")

    def test_reqrn_duration(self):
        slow_reqrn = epcstd.ReqRN(self.slow['rn'], self.slow['crc16'])
        fast_reqrn = epcstd.ReqRN(self.fast['rn'], self.fast['crc16'])
        slow_frame = epcstd.ReaderFrame(self.slow['sync'], slow_reqrn)
        fast_frame = epcstd.ReaderFrame(self.fast['sync'], fast_reqrn)

        self.assertAlmostEqual(
            slow_frame.duration,
            self.get_command_duration(epcstd.CommandCode.REQ_RN, self.slow),
            8, "command_duration(REQ_RN, slow) doesn't match frame")
        self.assertAlmostEqual(
            slow_frame.duration,
            epcstd.reqrn_duration(
                tari=self.slow['tari'], rtcal=self.slow['rtcal'],
                trcal=self.slow['trcal'], delim=self.slow['delim'],
                rn=self.slow['rn'], crc=self.slow['crc16']),
            8, "reqrn_duration(slow) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.duration,
            self.get_command_duration(epcstd.CommandCode.REQ_RN, self.fast),
            8, "command_duration(REQ_RN, fast) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.duration,
            epcstd.reqrn_duration(
                tari=self.fast['tari'], rtcal=self.fast['rtcal'],
                trcal=self.fast['trcal'], delim=self.fast['delim'],
                rn=self.fast['rn'], crc=self.fast['crc16']),
            8, "reqrn_duration(fast) doesn't match frame")

    def test_reqrn_duration_with_default_parameters(self):
        slow_reqrn = epcstd.ReqRN(self.slow['rn'], self.slow['crc16'])
        fast_reqrn = epcstd.ReqRN(self.fast['rn'], self.fast['crc16'])
        slow_frame = epcstd.ReaderFrame(self.slow['sync'], slow_reqrn)
        fast_frame = epcstd.ReaderFrame(self.fast['sync'], fast_reqrn)

        self.set_default_parameters(self.slow)

        self.assertAlmostEqual(
            slow_frame.duration,
            epcstd.command_duration(epcstd.CommandCode.REQ_RN), 8,
            "command_duration(REQ_RN, default=slow) doesn't match frame")
        self.assertAlmostEqual(
            slow_frame.duration, epcstd.reqrn_duration(), 8,
            "reqrn_duration(default=slow) doesn't match frame")

        self.set_default_parameters(self.fast)

        self.assertAlmostEqual(
            fast_frame.duration,
            epcstd.command_duration(epcstd.CommandCode.REQ_RN), 8,
            "command_duration(REQ_RN, default=fast) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.duration, epcstd.reqrn_duration(), 8,
            "reqrn_duration(default=fast) doesn't match frame")

    def test_read_duration(self):
        slow_read = epcstd.Read(self.slow['bank'], self.slow['word_ptr'],
                                self.slow['word_cnt'], self.slow['rn'],
                                self.slow['crc16'])
        fast_read = epcstd.Read(self.fast['bank'], self.fast['word_ptr'],
                                self.fast['word_cnt'], self.fast['rn'],
                                self.fast['crc16'])
        slow_frame = epcstd.ReaderFrame(self.slow['sync'], slow_read)
        fast_frame = epcstd.ReaderFrame(self.fast['sync'], fast_read)

        self.assertAlmostEqual(
            slow_frame.duration,
            self.get_command_duration(epcstd.CommandCode.READ, self.slow),
            8, "command_duration(READ, slow) doesn't match frame")
        self.assertAlmostEqual(
            slow_frame.duration,
            epcstd.read_duration(
                tari=self.slow['tari'], rtcal=self.slow['rtcal'],
                trcal=self.slow['trcal'], delim=self.slow['delim'],
                bank=self.slow['bank'], word_ptr=self.slow['word_ptr'],
                word_count=self.slow['word_cnt'], rn=self.slow['rn'],
                crc=self.slow['crc16']),
            8, "read_duration(slow params) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.duration,
            self.get_command_duration(epcstd.CommandCode.READ, self.fast),
            8, "command_duration(READ, fast) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.duration,
            epcstd.read_duration(
                tari=self.fast['tari'], rtcal=self.fast['rtcal'],
                trcal=self.fast['trcal'], delim=self.fast['delim'],
                bank=self.fast['bank'], word_ptr=self.fast['word_ptr'],
                word_count=self.fast['word_cnt'], rn=self.fast['rn'],
                crc=self.fast['crc16']),
            8, "read_duration(fast params) doesn't match frame")

    def test_read_duration_with_default_parameters(self):
        slow_read = epcstd.Read(self.slow['bank'], self.slow['word_ptr'],
                                self.slow['word_cnt'], self.slow['rn'],
                                self.slow['crc16'])
        fast_read = epcstd.Read(self.fast['bank'], self.fast['word_ptr'],
                                self.fast['word_cnt'], self.fast['rn'],
                                self.fast['crc16'])
        slow_frame = epcstd.ReaderFrame(self.slow['sync'], slow_read)
        fast_frame = epcstd.ReaderFrame(self.fast['sync'], fast_read)

        self.set_default_parameters(self.slow)

        self.assertAlmostEqual(
            slow_frame.duration,
            epcstd.command_duration(epcstd.CommandCode.READ), 8,
            "command_duration(READ, default=slow) doesn't match frame")
        self.assertAlmostEqual(
            slow_frame.duration, epcstd.read_duration(), 8,
            "read_duration(default=slow) doesn't match frame")

        self.set_default_parameters(self.fast)

        self.assertAlmostEqual(
            fast_frame.duration,
            epcstd.command_duration(epcstd.CommandCode.READ), 8,
            "command_duration(READ, default=fast) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.duration, epcstd.read_duration(), 8,
            "read_duration(default=fast) doesn't match frame")


class TestTagFrameAccessors(unittest.TestCase):
    def setUp(self):
        self.preambles = [epcstd.create_tag_preamble(m, trext)
                          for m in epcstd.TagEncoding
                          for trext in (True, False)]
        self.replies = [epcstd.QueryReply(), epcstd.AckReply(epc="01234567")]
        self.blfs = [40e3, 160e3, 360e3]

    def test_get_tag_frame_duration_equals_tag_frame_getter(self):
        for preamble in self.preambles:
            for reply in self.replies:
                for blf in self.blfs:
                    frame = epcstd.TagFrame(preamble, reply)
                    self.assertAlmostEqual(
                        epcstd.tag_frame_duration(
                            reply, blf, preamble.encoding, preamble.extended),
                        frame.get_duration(blf), 8)

    def test_get_tag_frame_duration_uses_default_modelParams(self):
        epcstd.stdParams.divide_ratio = epcstd.DivideRatio.DR_8
        for preamble in self.preambles:
            for reply in self.replies:
                for blf in self.blfs:
                    epcstd.stdParams.trext = preamble.extended
                    epcstd.stdParams.tag_encoding = preamble.encoding
                    epcstd.stdParams.trcal = \
                        epcstd.stdParams.divide_ratio.eval() / blf
                    frame = epcstd.TagFrame(preamble, reply)
                    self.assertAlmostEqual(
                        epcstd.tag_frame_duration(reply),
                        frame.get_duration(blf), 8, "frame = {}".format(frame))


class TestRepliesDurationEstimations(unittest.TestCase):
    """
    Test-cases for functions ``reply_duration``, ``query_reply_duration``,
    ``ack_reply_duration``, etc.
    """
    def setUp(self):
        self.slow = dict(dr=epcstd.DivideRatio.DR_8, trcal=225.0e-6,
                         encoding=epcstd.TagEncoding.M8, trext=True,
                         epc_bytelen=12, word_cnt=15)
        self.fast = dict(dr=epcstd.DivideRatio.DR_643, trcal=17.875e-6,
                         encoding=epcstd.TagEncoding.FM0, trext=False,
                         epc_bytelen=4, word_cnt=1)

        for par in [self.slow, self.fast]:
            par['blf'] = epcstd.get_blf(par['dr'], par['trcal'])
            par['preamble'] = epcstd.create_tag_preamble(
                par['encoding'], par['trext'])

    @staticmethod
    def get_reply_duration(reply_type, par):
        return epcstd.reply_duration(
            reply_type=reply_type, dr=par['dr'], trcal=par['trcal'],
            encoding=par['encoding'], trext=par['trext'],
            epc_bytelen=par['epc_bytelen'], words_count=par['word_cnt'])

    @staticmethod
    def set_default_parameters(par):
        epcstd.stdParams.divide_ratio = par['dr']
        epcstd.stdParams.trcal = par['trcal']
        epcstd.stdParams.tag_encoding = par['encoding']
        epcstd.stdParams.trext = par['trext']
        epcstd.stdParams.default_epc = "FF" * par['epc_bytelen']
        epcstd.stdParams.read_default_word_count = par['word_cnt']

    def test_query_reply_duration(self):
        reply = epcstd.QueryReply(0x0000)
        slow_frame = epcstd.TagFrame(self.slow['preamble'], reply)
        fast_frame = epcstd.TagFrame(self.fast['preamble'], reply)

        self.assertAlmostEqual(
            slow_frame.get_duration(self.slow['blf']),
            self.get_reply_duration(epcstd.ReplyType.QUERY_REPLY, self.slow),
            8, "reply_duration(QUERY_REPLY, slow) doesn't match frame")
        self.assertAlmostEqual(
            slow_frame.get_duration(self.slow['blf']),
            epcstd.query_reply_duration(
                dr=self.slow['dr'], trcal=self.slow['trcal'],
                encoding=self.slow['encoding'], trext=self.slow['trext']),
            8, "query_reply_duration(slow params) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.get_duration(self.fast['blf']),
            self.get_reply_duration(epcstd.ReplyType.QUERY_REPLY, self.fast),
            8, "reply_duration(QUERY_REPLY, fast) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.get_duration(self.fast['blf']),
            epcstd.query_reply_duration(
                self.fast['dr'], self.fast['trcal'], self.fast['encoding'],
                self.fast['trext']),
            8, "query_reply_duration(fast params) doesn't match frame")

    def test_query_reply_duration_with_default_parameters(self):
        reply = epcstd.QueryReply()
        slow_frame = epcstd.TagFrame(self.slow['preamble'], reply)
        fast_frame = epcstd.TagFrame(self.fast['preamble'], reply)

        self.set_default_parameters(self.slow)

        self.assertAlmostEqual(
            slow_frame.get_duration(self.slow['blf']),
            epcstd.reply_duration(epcstd.ReplyType.QUERY_REPLY), 8,
            "reply_duration(QUERY_REPLY, default=slow) doesn't match frame")
        self.assertAlmostEqual(
            slow_frame.get_duration(self.slow['blf']),
            epcstd.query_reply_duration(), 8,
            "query_reply_duration(default=slow) doesn't match frame")

        self.set_default_parameters(self.fast)

        self.assertAlmostEqual(
            fast_frame.get_duration(self.fast['blf']),
            epcstd.reply_duration(epcstd.ReplyType.QUERY_REPLY), 8,
            "reply_duration(QUERY_REPLY, default=fast) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.get_duration(self.fast['blf']),
            epcstd.query_reply_duration(), 8,
            "query_reply_duration(default=fast) doesn't match frame")

    def test_ack_reply_duration(self):
        slow_reply = epcstd.AckReply(epc=("FF" * self.slow['epc_bytelen']))
        fast_reply = epcstd.AckReply(epc=("FF" * self.fast['epc_bytelen']))
        slow_frame = epcstd.TagFrame(self.slow['preamble'], slow_reply)
        fast_frame = epcstd.TagFrame(self.fast['preamble'], fast_reply)

        self.assertAlmostEqual(
            slow_frame.get_duration(self.slow['blf']),
            self.get_reply_duration(epcstd.ReplyType.ACK_REPLY, self.slow),
            8, "reply_duration(ACK_REPLY, slow) doesn't match frame")
        self.assertAlmostEqual(
            slow_frame.get_duration(self.slow['blf']),
            epcstd.ack_reply_duration(
                dr=self.slow['dr'], trcal=self.slow['trcal'],
                encoding=self.slow['encoding'], trext=self.slow['trext'],
                epc_bytelen=self.slow['epc_bytelen']),
            8, "ack_reply_duration(slow params) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.get_duration(self.fast['blf']),
            self.get_reply_duration(epcstd.ReplyType.ACK_REPLY, self.fast),
            8, "reply_duration(ACK_REPLY, fast) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.get_duration(self.fast['blf']),
            epcstd.ack_reply_duration(
                dr=self.fast['dr'], trcal=self.fast['trcal'],
                encoding=self.fast['encoding'], trext=self.fast['trext'],
                epc_bytelen=self.fast['epc_bytelen']),
            8, "ack_reply_duration(fast params) doesn't match frame")

    def test_ack_reply_duration_with_default_parameters(self):
        slow_reply = epcstd.AckReply(epc=("FF" * self.slow['epc_bytelen']))
        fast_reply = epcstd.AckReply(epc=("FF" * self.fast['epc_bytelen']))
        slow_frame = epcstd.TagFrame(self.slow['preamble'], slow_reply)
        fast_frame = epcstd.TagFrame(self.fast['preamble'], fast_reply)

        self.set_default_parameters(self.slow)

        self.assertAlmostEqual(
            slow_frame.get_duration(self.slow['blf']),
            epcstd.reply_duration(epcstd.ReplyType.ACK_REPLY), 8,
            "reply_duration(ACK_REPLY, default=slow) doesn't match frame")
        self.assertAlmostEqual(
            slow_frame.get_duration(self.slow['blf']),
            epcstd.ack_reply_duration(), 8,
            "ack_reply_duration(default=slow) doesn't match frame")

        self.set_default_parameters(self.fast)

        self.assertAlmostEqual(
            fast_frame.get_duration(self.fast['blf']),
            epcstd.reply_duration(epcstd.ReplyType.ACK_REPLY), 8,
            "reply_duration(ACK_REPLY, default=fast) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.get_duration(self.fast['blf']),
            epcstd.ack_reply_duration(), 8,
            "ack_reply_duration(default=fast) doesn't match frame")

    def test_reqrn_reply_duration(self):
        reply = epcstd.ReqRnReply()
        slow_frame = epcstd.TagFrame(self.slow['preamble'], reply)
        fast_frame = epcstd.TagFrame(self.fast['preamble'], reply)

        self.assertAlmostEqual(
            slow_frame.get_duration(self.slow['blf']),
            self.get_reply_duration(epcstd.ReplyType.REQRN_REPLY, self.slow),
            8, "reply_duration(REQRN_REPLY, slow) doesn't match frame")
        self.assertAlmostEqual(
            slow_frame.get_duration(self.slow['blf']),
            epcstd.reqrn_reply_duration(
                dr=self.slow['dr'], trcal=self.slow['trcal'],
                encoding=self.slow['encoding'], trext=self.slow['trext']),
            8, "reqrn_reply_duration(slow params) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.get_duration(self.fast['blf']),
            self.get_reply_duration(epcstd.ReplyType.REQRN_REPLY, self.fast),
            8, "reply_duration(REQRN_REPLY, fast) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.get_duration(self.fast['blf']),
            epcstd.reqrn_reply_duration(
                dr=self.fast['dr'], trcal=self.fast['trcal'],
                encoding=self.fast['encoding'], trext=self.fast['trext']),
            8, "reqrn_reply_duration(fast params) doesn't match frame")

    def test_reqrn_reply_duration_with_default_parameters(self):
        reply = epcstd.ReqRnReply()
        slow_frame = epcstd.TagFrame(self.slow['preamble'], reply)
        fast_frame = epcstd.TagFrame(self.fast['preamble'], reply)

        self.set_default_parameters(self.slow)

        self.assertAlmostEqual(
            slow_frame.get_duration(self.slow['blf']),
            epcstd.reply_duration(epcstd.ReplyType.REQRN_REPLY), 8,
            "reply_duration(REQRN_REPLY, default=slow) doesn't match frame")
        self.assertAlmostEqual(
            slow_frame.get_duration(self.slow['blf']),
            epcstd.reqrn_reply_duration(), 8,
            "reqrn_reply_duration(default=slow) doesn't match frame")

        self.set_default_parameters(self.fast)

        self.assertAlmostEqual(
            fast_frame.get_duration(self.fast['blf']),
            epcstd.reply_duration(epcstd.ReplyType.REQRN_REPLY), 8,
            "reply_duration(REQRN_REPLY, default=fast) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.get_duration(self.fast['blf']),
            epcstd.reqrn_reply_duration(), 8,
            "reqrn_reply_duration(default=fast) doesn't match frame")

    def test_read_reply_duration(self):
        slow_reply = epcstd.ReadReply("FFFF" * self.slow['word_cnt'])
        fast_reply = epcstd.ReadReply("FFFF" * self.fast['word_cnt'])
        slow_frame = epcstd.TagFrame(self.slow['preamble'], slow_reply)
        fast_frame = epcstd.TagFrame(self.fast['preamble'], fast_reply)

        self.assertAlmostEqual(
            slow_frame.get_duration(self.slow['blf']),
            self.get_reply_duration(epcstd.ReplyType.READ_REPLY, self.slow),
            8, "reply_duration(READ_REPLY, slow) doesn't match frame")
        self.assertAlmostEqual(
            slow_frame.get_duration(self.slow['blf']),
            epcstd.read_reply_duration(
                dr=self.slow['dr'], trcal=self.slow['trcal'],
                encoding=self.slow['encoding'], trext=self.slow['trext'],
                words_count=self.slow['word_cnt']),
            8, "read_reply_duration(slow params) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.get_duration(self.fast['blf']),
            self.get_reply_duration(epcstd.ReplyType.READ_REPLY, self.fast),
            8, "reply_duration(READ_REPLY, fast) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.get_duration(self.fast['blf']),
            epcstd.read_reply_duration(
                dr=self.fast['dr'], trcal=self.fast['trcal'],
                encoding=self.fast['encoding'], trext=self.fast['trext'],
                words_count=self.fast['word_cnt']),
            8, "read_reply_duration(fast params) doesn't match frame")

    def test_read_reply_duration_with_default_parameters(self):
        slow_reply = epcstd.ReadReply("FFFF" * self.slow['word_cnt'])
        fast_reply = epcstd.ReadReply("FFFF" * self.fast['word_cnt'])
        slow_frame = epcstd.TagFrame(self.slow['preamble'], slow_reply)
        fast_frame = epcstd.TagFrame(self.fast['preamble'], fast_reply)

        self.set_default_parameters(self.slow)

        self.assertAlmostEqual(
            slow_frame.get_duration(self.slow['blf']),
            epcstd.reply_duration(epcstd.ReplyType.READ_REPLY), 8,
            "reply_duration(READ_REPLY, default=slow) doesn't match frame")
        self.assertAlmostEqual(
            slow_frame.get_duration(self.slow['blf']),
            epcstd.read_reply_duration(), 8,
            "read_reply_duration(default=slow) doesn't match frame")

        self.set_default_parameters(self.fast)

        self.assertAlmostEqual(
            fast_frame.get_duration(self.fast['blf']),
            epcstd.reply_duration(epcstd.ReplyType.READ_REPLY), 8,
            "reply_duration(READ_REPLY, default=fast) doesn't match frame")
        self.assertAlmostEqual(
            fast_frame.get_duration(self.fast['blf']),
            epcstd.read_reply_duration(), 8,
            "read_reply_duration(default=fast) doesn't match frame")


class TestFrequencyToleranceEstimator(unittest.TestCase):
    NUM_RANDOM_CHECKS = 5

    def assert_frt_node_values(self, node_values, dr, temp):
        for trcal, frt in node_values:
            self.assertAlmostEqual(
                epcstd.get_frt(trcal*1e-6, dr, temp), frt, 8,
                "trcal={} (table node)".format(trcal))

    def assert_frt_interval_values(self, interval_values, dr, temp):
        for lb, rb, frt in interval_values:
            low_trcal = lb * 1.011 * 1e-6
            top_trcal = rb * 0.989 * 1e-6
            self.assertAlmostEqual(
                epcstd.get_frt(low_trcal, dr, temp), frt, 8,
                "trcal={} (interval left bound)".format(low_trcal))
            self.assertAlmostEqual(
                epcstd.get_frt(top_trcal, dr, temp), frt, 8,
                "trcal={} (interval right bound)".format(top_trcal))
            for i in range(TestFrequencyToleranceEstimator.NUM_RANDOM_CHECKS):
                trcal = uniform(low_trcal, top_trcal)
                self.assertAlmostEqual(
                    epcstd.get_frt(trcal, dr, temp), frt, 8,
                    "trcal={} (interval random internal point)".format(trcal))

    def test_tolerance_for_dr643_nominal_temp(self):
        node_values = [(33.3, 0.15), (66.7, 0.1), (83.3, 0.1)]
        intervals = [(33.3, 66.7, 0.22), (66.7, 83.3, 0.12),
                     (83.3, 133.3, 0.1), (133.3, 200.0, 0.07),
                     (200.0, 225.0, 0.05)]
        self.assert_frt_node_values(
            node_values, epcstd.DivideRatio.DR_643, epcstd.TempRange.NOMINAL)
        self.assert_frt_interval_values(
            intervals, epcstd.DivideRatio.DR_643, epcstd.TempRange.NOMINAL)

    def test_tolerance_for_dr643_extended_temp(self):
        node_values = [(33.3, 0.15), (66.7, 0.15), (83.3, 0.1)]
        intervals = [(33.3, 66.7, 0.22), (66.7, 83.3, 0.15),
                     (83.3, 133.3, 0.12), (133.3, 200.0, 0.07),
                     (200.0, 225.0, 0.05)]
        self.assert_frt_node_values(
            node_values, epcstd.DivideRatio.DR_643, epcstd.TempRange.EXTENDED)
        self.assert_frt_interval_values(
            intervals, epcstd.DivideRatio.DR_643, epcstd.TempRange.EXTENDED)

    def test_tolerance_for_dr8_nominal_temp(self):
        node_values = [(25.0, 0.10), (31.25, 0.10), (50.0, 0.07)]
        intervals = [(17.2, 25.0, 0.19), (25.0, 31.25, 0.12),
                     (31.25, 50.0, 0.10), (50.0, 75.0, 0.07),
                     (75.0, 200.0, 0.04)]
        self.assert_frt_node_values(
            node_values, epcstd.DivideRatio.DR_8, epcstd.TempRange.NOMINAL)
        self.assert_frt_interval_values(
            intervals, epcstd.DivideRatio.DR_8, epcstd.TempRange.NOMINAL)

    def test_tolerance_for_dr8_extended_temp(self):
        node_values = [(25.0, 0.15), (31.25, 0.10), (50.0, 0.07)]
        intervals = [(17.2, 25.0, 0.19), (25.0, 31.25, 0.15),
                     (31.25, 50.0, 0.10), (50.0, 75.0, 0.07),
                     (75.0, 200.0, 0.04)]
        self.assert_frt_node_values(
            node_values, epcstd.DivideRatio.DR_8, epcstd.TempRange.EXTENDED)
        self.assert_frt_interval_values(
            intervals, epcstd.DivideRatio.DR_8, epcstd.TempRange.EXTENDED)

    def test_get_frt_uses_readerParams(self):
        epcstd.stdParams.temp_range = epcstd.TempRange.NOMINAL
        epcstd.stdParams.divide_ratio = epcstd.DivideRatio.DR_8
        epcstd.stdParams.trcal = 31.25e-6
        self.assertAlmostEqual(epcstd.get_frt(), 0.10, 3)

        epcstd.stdParams.temp_range = epcstd.TempRange.EXTENDED
        epcstd.stdParams.divide_ratio = epcstd.DivideRatio.DR_643
        epcstd.stdParams.trcal = 66.7e-6
        self.assertAlmostEqual(epcstd.get_frt(), 0.15, 3)


class TestLinkTimings(unittest.TestCase):
    class Timeouts:
        t1 = None
        t2 = None
        t3 = None
        t4 = None
        t5 = None
        t6 = None
        t7 = None

        def __getitem__(self, index):
            ts = [self.t1, self.t2, self.t3, self.t4, self.t5, self.t6, self.t7]
            if 1 <= index <= 7:
                return ts[index - 1]
            else:
                raise IndexError("timeout index must be between 1 and 7")

        def __setitem__(self, key, value):
            if key == 1:
                self.t1 = value
            elif key == 2:
                self.t2 = value
            elif key == 3:
                self.t3 = value
            elif key == 4:
                self.t4 = value
            elif key == 5:
                self.t5 = value
            elif key == 6:
                self.t6 = value
            elif key == 7:
                self.t7 = value
            else:
                raise IndexError("timeout index must be between 1 and 7")

    class TBounds:
        t_min = None
        t_max = None

        def __init__(self):
            self.t_min = TestLinkTimings.Timeouts()
            self.t_max = TestLinkTimings.Timeouts()

    def setUp(self):
        self.temp = epcstd.TempRange.NOMINAL
        self.slow_tari = 25.0e-6
        self.slow_rtcal = self.slow_tari * 3
        self.slow_trcal = self.slow_rtcal * 3
        self.slow_dr = epcstd.DivideRatio.DR_8
        self.slow_blf = epcstd.get_blf(self.slow_dr, self.slow_trcal)
        self.slow_frt = epcstd.get_frt(self.slow_trcal, self.slow_dr,
                                       self.temp)
        self.fast_tari = 6.25e-6
        self.fast_rtcal = self.fast_tari * 2.5
        self.fast_trcal = self.fast_rtcal * 1.1
        self.fast_dr = epcstd.DivideRatio.DR_643
        self.fast_blf = epcstd.get_blf(self.fast_dr, self.fast_trcal)
        self.fast_frt = epcstd.get_frt(self.fast_trcal, self.fast_dr,
                                       self.temp)

        self.expected_timeouts = {
            "slow": self.TBounds(),
            "fast": self.TBounds()
        }
        t_slow_min = self.expected_timeouts["slow"].t_min
        t_slow_max = self.expected_timeouts["slow"].t_max
        t_fast_min = self.expected_timeouts["fast"].t_min
        t_fast_max = self.expected_timeouts["fast"].t_max

        t_slow_min.t1 = 281.25e-6 * (1.0 - self.slow_frt) - 2e-6
        t_slow_min.t2 = 84.375e-06
        t_slow_min.t3 = 0.0
        t_slow_min.t4 = 150e-6
        t_slow_min.t5 = t_slow_min.t1
        t_slow_min.t6 = t_slow_min.t1
        t_slow_min.t7 = 562.5e-6

        t_fast_min.t1 = 15.625e-6 * (1.0 - self.fast_frt) - 2e-6
        t_fast_min.t2 = 2.4169921875e-06
        t_fast_min.t3 = 0.0
        t_fast_min.t4 = 31.25e-6
        t_fast_min.t5 = t_fast_min.t1
        t_fast_min.t6 = t_fast_min.t1
        t_fast_min.t7 = 250.0e-6

        t_slow_max.t1 = 281.25e-6 * (1.0 + self.slow_frt) + 2e-6
        t_slow_max.t2 = 562.5e-6
        t_slow_max.t5 = 20e-3
        t_slow_max.t6 = 20e-3
        t_slow_max.t7 = 20e-3

        t_fast_max.t1 = 15.625e-6 * (1.0 + self.fast_frt) + 2e-6
        t_fast_max.t2 = 16.11328125e-06
        t_fast_max.t5 = 20e-3
        t_fast_max.t6 = 20e-3
        t_fast_max.t7 = 20e-3

    #
    # HELPERS FOR TIMEOUTS CHECKS
    #

    def assertTimeoutsEqual(self, actual, expected, num_digits=8,
                            prefix="", suffix=""):
        for i in range(1, 8):
            if expected[i] is not None:
                self.assertAlmostEqual(actual[i], expected[i], num_digits,
                                       "{} T{}({})".format(prefix, i, suffix))

    def build_t_min(self, rtcal=None, trcal=None, dr=None, temp=None):
        ts = self.Timeouts()
        ts.t1 = epcstd.link_t1_min(rtcal=rtcal, trcal=trcal, dr=dr, temp=temp)
        ts.t2 = epcstd.link_t2_min(trcal=trcal, dr=dr)
        ts.t3 = epcstd.link_t3()
        ts.t4 = epcstd.link_t4(rtcal=rtcal)
        ts.t5 = epcstd.link_t5_min(rtcal=rtcal, trcal=trcal, dr=dr, temp=temp)
        ts.t6 = epcstd.link_t6_min(rtcal=rtcal, trcal=trcal, dr=dr, temp=temp)
        ts.t7 = epcstd.link_t7_min(trcal=trcal, dr=dr)
        return ts

    def build_t_max(self, rtcal=None, trcal=None, dr=None, temp=None):
        ts = self.Timeouts()
        ts.t1 = epcstd.link_t1_max(rtcal=rtcal, trcal=trcal, dr=dr, temp=temp)
        ts.t2 = epcstd.link_t2_max(trcal=trcal, dr=dr)
        ts.t5 = epcstd.link_t5_max()
        ts.t6 = epcstd.link_t6_max()
        ts.t7 = epcstd.link_t7_max()
        return ts

    def build_t_min_with_universal_getter(
            self, rtcal=None, trcal=None, dr=None, temp=None):
        ts = self.Timeouts()
        for i in range(1, 8):
            ts[i] = epcstd.min_link_t(i, rtcal=rtcal, trcal=trcal, dr=dr,
                                      temp=temp)
        return ts

    def build_t_max_with_universal_getter(
            self, rtcal=None, trcal=None, dr=None, temp=None):
        ts = self.Timeouts()
        for i in [1, 2, 5, 6, 7]:
            ts[i] = epcstd.max_link_t(i, rtcal=rtcal, trcal=trcal, dr=dr,
                                      temp=temp)
        return ts

    @staticmethod
    def set_default_modelParams(rtcal, trcal, dr, temp):
        epcstd.stdParams.rtcal = rtcal
        epcstd.stdParams.trcal = trcal
        epcstd.stdParams.divide_ratio = dr
        epcstd.stdParams.temp_range = temp

    #
    # TESTS
    #

    def test_get_pri_with_explicit_parameters(self):
        self.assertAlmostEqual(
            epcstd.get_pri(trcal=self.slow_trcal, dr=self.slow_dr),
            1.0 / self.slow_blf, 8)
        self.assertAlmostEqual(
            epcstd.get_pri(trcal=self.fast_trcal, dr=self.fast_dr),
            1.0 / self.fast_blf, 8)

    def test_get_pri_with_implicit_parameters_from_readerParams(self):
        epcstd.stdParams.trcal = self.slow_trcal
        epcstd.stdParams.divide_ratio = self.slow_dr
        self.assertAlmostEqual(epcstd.get_pri(), 1.0 / self.slow_blf, 8)

        epcstd.stdParams.trcal = self.fast_trcal
        epcstd.stdParams.divide_ratio = self.fast_dr
        self.assertAlmostEqual(epcstd.get_pri(), 1.0 / self.fast_blf, 8)

    def test_custom_get_tX_min_with_explicit_parameters(self):
        actual_timeouts = {
            "slow": self.build_t_min(self.slow_rtcal, self.slow_trcal,
                                     self.slow_dr, self.temp),
            "fast": self.build_t_min(self.fast_rtcal, self.fast_trcal,
                                     self.fast_dr, self.temp)
        }
        for key in ["slow", "fast"]:
            self.assertTimeoutsEqual(
                actual_timeouts[key], self.expected_timeouts[key].t_min,
                prefix=key, suffix="min")

    def test_custom_get_tX_max_with_explicit_parameters(self):
        actual_timeouts = {
            "slow": self.build_t_max(self.slow_rtcal, self.slow_trcal,
                                     self.slow_dr, self.temp),
            "fast": self.build_t_max(self.fast_rtcal, self.fast_trcal,
                                     self.fast_dr, self.temp)
        }
        for key in ["slow", "fast"]:
            self.assertTimeoutsEqual(
                actual_timeouts[key], self.expected_timeouts[key].t_max,
                prefix=key, suffix="max")

    def test_custom_get_tX_with_implicit_parameters_from_modelParams(self):
        # Setting up slow link parameters
        self.set_default_modelParams(self.slow_rtcal, self.slow_trcal,
                                     self.slow_dr, self.temp)
        t_min = self.build_t_min()  # leaving all parameters None
        t_max = self.build_t_max()  # leaving all parameters None
        self.assertTimeoutsEqual(t_min, self.expected_timeouts["slow"].t_min,
                                 prefix="default slow", suffix="min")
        self.assertTimeoutsEqual(t_max, self.expected_timeouts["slow"].t_max,
                                 prefix="default slow", suffix="max")

        # Setting up fast link parameters
        self.set_default_modelParams(self.fast_rtcal, self.fast_trcal,
                                     self.fast_dr, self.temp)
        t_min = self.build_t_min()  # leaving all parameters None
        t_max = self.build_t_max()  # leaving all parameters None
        self.assertTimeoutsEqual(t_min, self.expected_timeouts["fast"].t_min,
                                 prefix="default fast", suffix="min")
        self.assertTimeoutsEqual(t_max, self.expected_timeouts["fast"].t_max,
                                 prefix="default fast", suffix="max")

    def test_universal_get_t_min_with_explicit_parameters(self):
        actual_timeouts = {
            "slow": self.build_t_min_with_universal_getter(
                self.slow_rtcal, self.slow_trcal, self.slow_dr, self.temp),
            "fast": self.build_t_min_with_universal_getter(
                self.fast_rtcal, self.fast_trcal, self.fast_dr, self.temp),
        }

        for key in ['slow', 'fast']:
            self.assertTimeoutsEqual(
                actual_timeouts[key], self.expected_timeouts[key].t_min,
                num_digits=8, prefix=key, suffix="min")

        # Check that get_t_min works for n=1..7 only
        with self.assertRaises(ValueError):
            epcstd.min_link_t(
                0, self.slow_rtcal, self.slow_trcal, self.slow_dr, self.temp)
            epcstd.min_link_t(
                8, self.slow_rtcal, self.slow_trcal, self.slow_dr, self.temp)

    def test_universal_get_t_max_with_explicit_parameters(self):
        actual_timeouts = {
            "slow": self.build_t_max_with_universal_getter(
                self.slow_rtcal, self.slow_trcal, self.slow_dr, self.temp),
            "fast": self.build_t_max_with_universal_getter(
                self.fast_rtcal, self.fast_trcal, self.fast_dr, self.temp),
        }

        for key in ["slow", "fast"]:
            self.assertTimeoutsEqual(
                actual_timeouts[key], self.expected_timeouts[key].t_max,
                num_digits=8, prefix=key, suffix="max")

        self.assertAlmostEqual(
            epcstd.max_link_t(3, self.slow_rtcal, self.slow_trcal, self.slow_dr,
                              self.temp), float('inf'))

        # Check that get_t_max works for n=1..7, n != 3 only
        with self.assertRaises(ValueError):
            epcstd.max_link_t(0, self.slow_rtcal, self.slow_trcal, self.slow_dr,
                              self.temp)
            epcstd.max_link_t(8, self.slow_rtcal, self.slow_trcal, self.slow_dr,
                              self.temp)

    def test_universal_get_t_min_with_parameters_from_modelParams(self):
        # Setting up slow parameters
        self.set_default_modelParams(self.slow_rtcal, self.slow_trcal,
                                     self.slow_dr, self.temp)
        slow = self.build_t_min_with_universal_getter()
        self.assertTimeoutsEqual(slow, self.expected_timeouts["slow"].t_min,
                                 prefix="slow", suffix="min")

        # Setting up fast parameters
        self.set_default_modelParams(self.fast_rtcal, self.fast_trcal,
                                     self.fast_dr, self.temp)
        fast = self.build_t_min_with_universal_getter()
        self.assertTimeoutsEqual(fast, self.expected_timeouts['fast'].t_min,
                                 prefix="fast", suffix="min")

    def test_universal_get_t_max_with_parameters_from_modelParams(self):
        # Setting up slow parameters
        self.set_default_modelParams(self.slow_rtcal, self.slow_trcal,
                                     self.slow_dr, self.temp)
        slow = self.build_t_max_with_universal_getter()
        self.assertTimeoutsEqual(slow, self.expected_timeouts["slow"].t_max,
                                 prefix="slow", suffix="max")

        # Setting up fast parameters
        self.set_default_modelParams(self.fast_rtcal, self.fast_trcal,
                                     self.fast_dr, self.temp)
        fast = self.build_t_max_with_universal_getter()
        self.assertTimeoutsEqual(fast, self.expected_timeouts['fast'].t_max,
                                 prefix="fast", suffix="max")


class TestElementaryTimings(unittest.TestCase):
    def setUp(self):
        self.fast_tari = 6.25e-6
        self.fast_rtcal = 15.625e-6
        self.fast_trcal = 17.875e-6
        self.fast_trext = False
        self.fast_temp = epcstd.TempRange.NOMINAL
        self.fast_q = 4
        self.fast_dr = epcstd.DivideRatio.DR_643
        self.fast_m = epcstd.TagEncoding.FM0
        self.fast_target = epcstd.InventoryFlag.A
        self.fast_sel = epcstd.SelFlag.ALL
        self.fast_session = epcstd.Session.S0
        self.fast_bank = epcstd.MemoryBank.TID
        self.fast_word_ptr = 0
        self.fast_word_count = 4
        self.fast_data = "89ABCDEF"
        self.fast_epc = "00112233445566778899AABB"
        self.fast_pc = 0x0000
        self.fast_rn = 0x0000
        self.fast_crc = 0x0000
        self.fast_t = {
            "Query": 199.125e-6,
            "QueryRep": 59.375e-6,
            "ACK": 150.0e-6,
            "ReqRN": 293.75e-6,
            "Read": 412.5e-6,
            "T1(min)": 11.28125e-6,
            "T1(max)": 19.96875e-6,
            "T2(min)": 2.51367188e-6,
            "T2(max)": 16.7578125e-6,
            "T3(min)": 0.0e-6,
            "T3(max)": float("inf"),
            "T4(min)": 31.25e-6,
            "T4(max)": float("inf"),
            "RN16": 19.27148438e-6,
            "Response": 113.11523438e-6,
            "Handle": 32.67773438e-6,
            "Data": 60.328125e-6
        }

    def test_get_elementary_timings(self):
        d = epcstd.get_elementary_timings(
            tari=self.fast_tari, rtcal=self.fast_rtcal, trcal=self.fast_trcal,
            temp=self.fast_temp, dr=epcstd.DivideRatio.DR_643,
            m=self.fast_m, trext=self.fast_trext, sel=self.fast_sel,
            session=self.fast_session, target=self.fast_target, q=self.fast_q,
            bank=self.fast_bank, word_ptr=self.fast_word_ptr,
            word_count=self.fast_word_count, rn=self.fast_rn,
            crc=self.fast_crc, epc=self.fast_epc, mem=self.fast_data,
            pc=self.fast_pc)
        for k, v in self.fast_t.items():
            self.assertIn(k, d, "key {} not found in timings".format(k))
            self.assertAlmostEqual(v, d[k], 8, "error in {}".format(k))

