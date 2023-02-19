# Make via
proc mkvia12 {} {
  set bsize [magic::box size]
  set w [lindex $bsize 0]
  set l [lindex $bsize 1]
  # Convert from lambda to internal units
  set w [expr $w / 200.0]
  set l [expr $l / 200.0]
  puts "Creating VIA12 in: [expr $w] [expr $l]"
  if {($w < 0.26) ||  ($l < 0.26)} {
    puts "$w $l too small for one via"
    return -1
  }
  set wd [expr ($w - 0.26) / ( 2 * 0.26)]
  set ld [expr ($l - 0.26) / ( 2 * 0.26)]
  set wx [expr ($wd - floor($wd))/2]
  set lx [expr ($ld - floor($ld))/2]
  # get aligned values
  set wd [expr floor($wd) + 1]
  set ld [expr floor($ld) + 1]
  set wx_half [expr 0.005 * round($wx / 0.005)]
  set lx_half [expr 0.005 * round($lx / 0.005)]
  puts "$wd $ld"
  puts "$wx_half $lx_half"
  puts [expr $wd * (0.26*2) - 0.26]
  puts [expr $ld * (0.26*2) - 0.26]
  
  magic::box size 0.26um 0.26um
  for {set x 0} {$x < $wd} {incr x} {
    for {set y 0} {$y < $ld} {incr y} {
      magic::paint v1
      magic::box move up 0.52um
    }
    magic::box move down [expr 0.52 * $ld]um
    magic::box move right 0.52um
  }
  magic::box move left [expr 0.52 * $wd]um
  magic::box size [expr $wd * (0.26*2) - 0.26]um [expr $ld * (0.26*2) - 0.26]um
  if {$l > $w} {
    magic::box grow top 0.01um
    magic::box grow bottom 0.01um
    magic::box grow left 0.06um
    magic::box grow right 0.06um
  } else {
    magic::box grow top 0.06um
    magic::box grow bottom 0.06um
    magic::box grow left 0.01um
    magic::box grow right 0.01um
  }
  magic::paint m1
  magic::paint m2
}
