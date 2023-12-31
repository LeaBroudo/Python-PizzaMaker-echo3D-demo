/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file pStatThreadData.I
 * @author drose
 * @date 2000-07-10
 */

/**
 * Returns a pointer to the ClientData structure associated with this data.
 */
INLINE const PStatClientData *PStatThreadData::
get_client_data() const {
  return _client_data;
}

/**
 * Returns true if the structure contains no frames, false otherwise.
 */
INLINE bool PStatThreadData::
is_empty() const {
  return _frames.empty();
}
