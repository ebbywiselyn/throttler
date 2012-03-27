#!/usr/bin/env python
#
# Copyright (C) 2011 Ebby Wiselyn
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


__author__ = 'ebbywiselyn@gmail.com (Ebby Wiselyn)'


import math
import optparse
import select
import signal
import sys
import time


class Throttle(object):
  """ Throttle provides data rate throttling

      valve interval specifies the outlet interval, which defaults to 10
      Timing is done using 3 timers with varying levels of precision,

      unit_timer = 1 sec
      deci_timer = 0.1 sec
      centi_timer = 0.01 sec
  """


  def __init__(self, config):
    """Creates a Throttle Object and provides data rate throttling .
    Args:
      config: [Conf] The configuration of the Throttle specified by the 
              Config Object. Config should have data rate, precision of the timer 
              duration of the throttle valve events, data fragment and block sizes. 
 
    Yields:
      A Throttle Object with the specified configuration 
    """

    self.conf = config
    self.valve_intvl = 10
    self.data = ''

    self.unit_timer = 0
    self.deci_timer = 0
    self.centi_timer = 1

  def _UnitOutlet(self):
    """Streams data in frag_size in the interval specified by centi_timer"""
    conf = self.conf
    centi_dur = 0.01

    while self.centi_timer <= self.valve_intvl:  
      start = time.time()

      if conf.block_size > conf.frag_size:
        self.data = sys.stdin.read(int(conf.frag_size))
        if not self.data:
          conf.end_of_input = True
          return
        sys.stdout.write(self.data)
        conf.block_size = conf.block_size - conf.frag_size
      else:
        self.data = sys.stdin.read(int(conf.block_size))
        if not self.data:
          conf.end_of_input = True
          return
        sys.stdout.write(self.data)
      
      end = time.time()
      dur = end - start
      prec = conf.precision / 10
      real_time = (self.unit_timer * 100 + 
                   self.deci_time * 10 + 
                   self.centi_timer) * prec
      self.centi_timer += 1
      exec_time = time.time() - conf.init_time 
     
      if dur < centi_dur and real_time > exec_time:
        time.sleep(real_time - exec_time)

    self.centi_timer = 1
    conf.block_size = math.ceil(conf.rate * conf.precision)

  
  def Throttling(self):
    """Streams the input at specified rate 
    Args: 
      None
      
    Yields:
      Data stream at specified rate
    """
    conf = self.conf 
    input_streaming = True
    self.unit_timer = 0

    while input_streaming:
      try:
        [read_obj, _, _] = select.select([sys.stdin], [], [])
      except select.error, IOError:
        print 'Error while reading standard input'
        sys.exit(2)
      
      if not read_obj:
        input_streaming = False
        continue
     
      [self._UnitOutlet() for self.deci_time in 
          range(0, self.valve_intvl) 
              if not conf.end_of_input]
 
      if not self.data:
        input_streaming = False

      self.unit_timer = self.unit_timer + 1


def _GenerateConfig(options, init_time, name='Object'):
  """Dynamically generates a Config Object.
  Based on the options provided
  Args:
    options: [instance] List of options from the user
    init_time: [float] Start time of the application 
    name: [string] Name of the Config object to be generated 
          defaults to 'Object'

  Yields:
    A Data Object with required arguments
  """
   
  valve_intvl = 10
  precision = 1.0 / value_intvl
  dur = precision / valve_intvl
  rate = options.byte

  block_size = (math.ceil(rate * precision)) 
  frag_size = (math.ceil(block_size / valve_intvl))
  end_of_input = False
  
  
  c = dict([('rate', options.byte), ('precision', precision), 
            ('dur', dur), ('block_size', block_size), 
            ('frag_size', frag_size), ('end_of_input', end_of_input), ('init_time', init_time)])
  
  return type(name, (), c)    


def _UnitsConvert(options):
  """Convert between units.
  Args:
    options [instance]: command line options
   
  Returns:
    options [instance]: Returns options object.  
            with the units converted 
  """

  byte_s = 1024
  default = 10
 
  if options.kibi_bit:
    options.byte = options.kibi_bit * 128
  elif options.kibi_byte:
    options.byte = options.kibi_byte * byte_s
  elif options.byte:
    options.byte = options.byte
  else:
    options.byte = default * byte_s

  return options


def main():
  """Runs the Throttle application with the provided input."""
  init_time = time.time()
  parser = optparse.OptionParser(usage=
                                 "%prog [options]")
  group = parser.add_option_group("Data options")
  group.add_option("-b", "--bytes", action="store", type="int", 
                   dest="byte", help="bytes per second")
  group.add_option("-k", "--kibibit", action="store", type="int", 
                   dest="kibi_bit", help="kibibits per second")
  group.add_option("-K", "--kibibyte", action="store", type="int", 
                   dest="kibi_byte", help="kilobytes per second")
  try:
    options, args = parser.parse_args(sys.argv[1:])
  except optparse.OptionError, TypeError:
    print 'Usage %prog [options]'
    sys.exit(2)

  options = _UnitsConvert (options)
  Conf = _GenerateConfig(options, init_time, name='Config')
  throttle = Throttle(Conf())
  throttle.Throttling()

if __name__ == '__main__':
  main()
