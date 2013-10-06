# vim: set ts=8 sts=2 sw=2 tw=99 et:
#
# This file is part of AMBuild.
# 
# AMBuild is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# AMBuild is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with AMBuild. If not, see <http://www.gnu.org/licenses/>.
import os, sys, util
from . import process

if util.IsWindows():
  import ipc.windows as ipc_impl
elif util.IsLinux():
  import ipc.linux as ipc_impl
elif util.IsBSD():
  import ipc.bsd as ipc_impl
else:
  raise Exception('Unknown platform: ' + util.Platform())

ProcessManager = ipc_impl.ProcessManager
MessagePump = ipc_impl.MessagePump

class ChildWrapperListener(process.MessageListener):
  def __init__(self, listener):
    super(ChildWrapperListener, self).__init__()
    self.listener = listener

  def receiveConnected(self, channel):
    self.listener.receiveConnected(channel)

  def receiveMessage(self, channel, message):
    self.listener.receiveMessage(message)

  def receiveError(self, channel, error):
    self.listener.receiveError(error)
    sys.stderr.write('Parent process died, terminating...\n')
    sys.exit(1)

def child_main(channel):
  print('Child process spawned: ' + str(os.getpid()))
  message = channel.recv()
  assert(message['id'] == 'start')

  target = message['target']
  listener_type = message['listener_type']
  args = message['args']
  channels = ()
  if 'channels' in message:
    channels = message['channels']
  
  mp = MessagePump()
  listener = listener_type(mp, *(args + channels))
  listener = ChildWrapperListener(listener)
  mp.addChannel(channel, listener)
  channel.send(Special.Connected)
  listener.receiveConnected(channel)
  mp.pump()
