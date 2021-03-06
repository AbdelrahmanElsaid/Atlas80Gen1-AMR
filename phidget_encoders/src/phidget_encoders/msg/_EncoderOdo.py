"""autogenerated by genpy from phidget_encoders/EncoderOdo.msg. Do not edit."""
import sys
python3 = True if sys.hexversion > 0x03000000 else False
import genpy
import struct

import genpy

class EncoderOdo(genpy.Message):
  _md5sum = "0d55fd3a8687a0b84ac8936be8804b2c"
  _type = "phidget_encoders/EncoderOdo"
  _has_header = False #flag to mark the presence of a Header object
  _full_text = """time stamp

# time since previous message (as measured by the encoders)
float64 dt

# traveled distance by the car
float64 d_dist
float64 d_th

# velocities
float64 v
float64 w
"""
  __slots__ = ['stamp','dt','d_dist','d_th','v','w']
  _slot_types = ['time','float64','float64','float64','float64','float64']

  def __init__(self, *args, **kwds):
    """
    Constructor. Any message fields that are implicitly/explicitly
    set to None will be assigned a default value. The recommend
    use is keyword arguments as this is more robust to future message
    changes.  You cannot mix in-order arguments and keyword arguments.

    The available fields are:
       stamp,dt,d_dist,d_th,v,w

    :param args: complete set of field values, in .msg order
    :param kwds: use keyword arguments corresponding to message field names
    to set specific fields.
    """
    if args or kwds:
      super(EncoderOdo, self).__init__(*args, **kwds)
      #message fields cannot be None, assign default values for those that are
      if self.stamp is None:
        self.stamp = genpy.Time()
      if self.dt is None:
        self.dt = 0.
      if self.d_dist is None:
        self.d_dist = 0.
      if self.d_th is None:
        self.d_th = 0.
      if self.v is None:
        self.v = 0.
      if self.w is None:
        self.w = 0.
    else:
      self.stamp = genpy.Time()
      self.dt = 0.
      self.d_dist = 0.
      self.d_th = 0.
      self.v = 0.
      self.w = 0.

  def _get_types(self):
    """
    internal API method
    """
    return self._slot_types

  def serialize(self, buff):
    """
    serialize message into buffer
    :param buff: buffer, ``StringIO``
    """
    try:
      _x = self
      buff.write(_struct_2I5d.pack(_x.stamp.secs, _x.stamp.nsecs, _x.dt, _x.d_dist, _x.d_th, _x.v, _x.w))
    except struct.error as se: self._check_types(struct.error("%s: '%s' when writing '%s'" % (type(se), str(se), str(_x))))
    except TypeError as te: self._check_types(ValueError("%s: '%s' when writing '%s'" % (type(te), str(te), str(_x))))

  def deserialize(self, str):
    """
    unpack serialized message in str into this message instance
    :param str: byte array of serialized message, ``str``
    """
    try:
      if self.stamp is None:
        self.stamp = genpy.Time()
      end = 0
      _x = self
      start = end
      end += 48
      (_x.stamp.secs, _x.stamp.nsecs, _x.dt, _x.d_dist, _x.d_th, _x.v, _x.w,) = _struct_2I5d.unpack(str[start:end])
      self.stamp.canon()
      return self
    except struct.error as e:
      raise genpy.DeserializationError(e) #most likely buffer underfill


  def serialize_numpy(self, buff, numpy):
    """
    serialize message with numpy array types into buffer
    :param buff: buffer, ``StringIO``
    :param numpy: numpy python module
    """
    try:
      _x = self
      buff.write(_struct_2I5d.pack(_x.stamp.secs, _x.stamp.nsecs, _x.dt, _x.d_dist, _x.d_th, _x.v, _x.w))
    except struct.error as se: self._check_types(struct.error("%s: '%s' when writing '%s'" % (type(se), str(se), str(_x))))
    except TypeError as te: self._check_types(ValueError("%s: '%s' when writing '%s'" % (type(te), str(te), str(_x))))

  def deserialize_numpy(self, str, numpy):
    """
    unpack serialized message in str into this message instance using numpy for array types
    :param str: byte array of serialized message, ``str``
    :param numpy: numpy python module
    """
    try:
      if self.stamp is None:
        self.stamp = genpy.Time()
      end = 0
      _x = self
      start = end
      end += 48
      (_x.stamp.secs, _x.stamp.nsecs, _x.dt, _x.d_dist, _x.d_th, _x.v, _x.w,) = _struct_2I5d.unpack(str[start:end])
      self.stamp.canon()
      return self
    except struct.error as e:
      raise genpy.DeserializationError(e) #most likely buffer underfill

_struct_I = genpy.struct_I
_struct_2I5d = struct.Struct("<2I5d")
