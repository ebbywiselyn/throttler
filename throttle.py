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


  def __init__(self, options, init_time):
    """Creates a Throttle Object and provides data rate throttling .
    Args:
      config: [Conf] The configuration of the Throttle specified by the 
              Config Object. Config should have data rate, precision of the timer 
              duration of the throttle valve events, data fragment and block sizes. 
 
    Yields:
      A Throttle Object with the specified configuration 
    """

    self.data = ''
    self.valve_intvl = 10
    self.precision = 1.0 / self.valve_intvl
    self.dur = self.precision / self.valve_intvl
    self.rate = options.byte

    self.block_size = (math.ceil(self.rate * self.precision)) 
    self.frag_size = (math.ceil(self.block_size / self.valve_intvl))
    self.end_of_input = False

    self.unit_timer = 0
    self.deci_timer = 0
    self.centi_timer = 1
    self.init_time = init_time
    

  def _UnitOutlet(self):
    """Streams data in frag_size in the interval specified by centi_timer"""
    centi_dur = 0.01

    while self.centi_timer <= self.valve_intvl:  
      start = time.time()

      if self.block_size > self.frag_size:
        self.data = sys.stdin.read(int(self.frag_size))
        if not self.data:
          self.end_of_input = True
          return
        sys.stdout.write(self.data)
        self.block_size = self.block_size - self.frag_size
      else:
        self.data = sys.stdin.read(int(self.block_size))
        if not self.data:
          self.end_of_input = True
          return
        sys.stdout.write(self.data)
      
      end = time.time()
      dur = end - start
      prec = self.precision / 10
      real_time = (self.unit_timer * 100 + 
                   self.deci_time * 10 + 
                   self.centi_timer) * prec
      self.centi_timer += 1
      exec_time = time.time() - self.init_time 
     
      if dur < centi_dur and real_time > exec_time:
        time.sleep(real_time - exec_time)

    self.centi_timer = 1
    self.block_size = math.ceil(self.rate * self.precision)

  
  def Throttling(self):
    """Streams the input at specified rate 
    Args: 
      None
      
    Yields:
      Data stream at specified rate
    """
    input_streaming = True

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
              if not self.end_of_input]
 
      if not self.data:
        input_streaming = False

      self.unit_timer = self.unit_timer + 1


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
  throttle = Throttle(options, init_time)
  throttle.Throttling()

if __name__ == '__main__':
  main()
