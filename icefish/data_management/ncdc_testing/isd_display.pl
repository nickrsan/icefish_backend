#!/usr/local/bin/perl
#---- AUTHOR:  Fred Smith  fred.smith@noaa.gov
#     TMC Inc. - Government Contractor
#     National Climatic Data Center
#     http://www.ncdc.noaa.gov
#     Nov,2005.

#---- Author's perl packages directory exported externally in environment
#     variable "$FPATH" (technique removes need for hard-coded lib path names
#     in perl script):
use lib qw(C:/Users/dsx/Downloads);

#---- Note:  Set the directory pathname that contains your perl packages
#     (or where you placed the accompanying perl package "Cl_args.pm" OR
#      use author's technique above):
#use lib qw(path_to_where_"Cl_args.pm"_resides);

#---- At command line, set execute bits as follows for isd_display.pl:
#     chmod +x isd_display.pl<enter>"

#---- Script invocation:
#     isd_display.pl<enter>      (brief   help)
#     isd_display.pl help<enter> (verbose help)
#-------------------------------------------------------------------------------
use integer;
#---- CDS/MDS section byte offset, field length and field names:
@CDS_MDS=
( 0, 4, 'var_length',         # begin CDS section
  4, 6, 'usaf_id',
 10, 5, 'wban',
 15, 8, 'date',
 23, 4, 'gmt',                # "gmt" = Greenwich Mean Time
 27, 1, 'data_source',
 28, 6, 'lat',
 34, 7, 'long',
 41, 5, 'report_type',
 46, 5, 'elev',
 51, 5, 'call_letters',
 56, 4, 'qc_level',
 60, 3, 'wind_dir',            # begin MDS section
 63, 1, 'wind_dir_flag',
 64, 1, 'wind_type',
 65, 4, 'wind_speed',
 69, 1, 'wind_speed_flag',
 70, 5, 'sky_ceiling',
 75, 1, 'sky_ceil_flag',
 76, 1, 'sky_ceil_determ',
 77, 1, 'sky_cavok',
 78, 6, 'visibility',
 84, 1, 'vis_flag',
 85, 1, 'vis_var',
 86, 1, 'vis_var_flag',
 87, 5, 'air_temp',
 92, 1, 'air_temp_flag',
 93, 5, 'dew_point',
 98, 1, 'dew_point_flag',
 99, 5, 'sea_lev_press',
104, 1, 'sea_levp_flag',
999, 0, 'END-OF-TABLE'
);

#---- ADDitional section element mnemonic definitions and field lengths:
%add=
(AA=>11, AB=>10, AC=> 6, AD=>22, AE=>15, AG=> 7, AH=>18, AI=>18, AJ=>17, AK=>15,
 AL=>10, AM=>20, AN=>12, AT=>3, AU=>11, AW=> 6, AX=> 9, AY=> 8, AZ=> 8, ED=>11, GA=>16,
 GD=>15, GE=>7, GF=>26, GG=>18, GJ=> 8, GL=> 9, GK=> 7, HL=> 7, KA=>13, KB=>13, KC=>17,
 KD=>12, KE=>15, MA=>15, MD=>14, ME=> 9, MG=>15, MH=>15, MK=>27, MV=> 6, MW=> 6,
 OA=>11, OC=> 8, OD=>14, OE=>19, SA=> 8, UA=>13, UG=>12, WA=> 9, WD=>23, WG=>14,
 IA1=>6, IA2=>12
);
#-------------------------------------------------------------------------------
#---- Define command-line arguments, requirements, notes and defaults:
use Cl_args;
$TITLE='Display isd/ish records (CDS&MDS/ADD/REM/EQD/QNN sections are selectable)';
$all=qq/ default is "all/;
cl_args
( $ifn, 'ifn=',  'r', 'ifn=input_file_name'
 ,$rcds,'rcds=', 'o', 'rcds=(select records, e.g., rcds=1,18,100,...,'.$all
 ,$flds,'flds=', 'o', 'flds=(e.g., date,gmt,data_source,... - use "def" help switch)'
 ,undef,undef,   'n', 'select the following for any combination of sections.'.$all
 ,$cds, 'cds',   's', 'cds (display CDS & MDS section)'
 ,$add, 'add',   's', 'add (display ADD section)'
 ,$rem, 'rem',   's', 'rem (display REM section)'
 ,$eqd, 'eqd',   's', 'eqd (display EQD section)'
 ,$qnn, 'qnn',   's', 'qnn (display QNN section)'
 ,undef,undef,   'n', 'The following switches permit suppression of header lines'
 ,$nfn, 'nfn',   's', 'nfn (suppress "FILENAME   =..." in record display)'
 ,$nsn, 'nsn',   's', 'nsn (supress section name display: e.g., "ADD (rcd=...)")'
 ,undef,undef,   'n', 'The following are mutually exclusive with all the above'
 ,$def, 'def',   'h', 'def (displays CDS/MDS fixed position fields)'
 ,$adh, 'adh',   'h', 'adh (display ADD section field definitions)'
 ,$help,'help',  'h', 'help (verbose help)'
 );

#---- Perform helps if specified on command line:
if($def)
  {print "CDS/MDS field name definitions:\npos len  Name\n";
   for($i=0;$CDS_MDS[$i]<999;$i+=3)
     {printf "%3i %3i  %s\n",$CDS_MDS[$i]+1, $CDS_MDS[$i+1], $CDS_MDS[$i+2];}
  }
if($adh)
  {print "ADD section defined fields:\nele  len\n"; 
   foreach $k (sort keys %add){printf "%-3s = %2i\n",$k,$add{$k};}
  } 
if($help){system "perldoc $0\n";}
if($help || $def || $adh){exit 0;}

#---- Source file check:
$E='';
if($ifn){if(! -T $ifn){Emsg (qq/file "$ifn" - $!/);}}

#---- Check for switch inconsistancies:
$all='';if(!($hdr || $cds || $add || $rem || $eqd || $qnn))
  {if(!$flds){$all=1;}}

#---- Exit on errors in command-line processing:
$E && exit 1;
#-------------------------------------------------------------------------------
#---- Initializations:
if($all){$hdr=$cds=$add=$rem=$eqd=$qnn=1;}	# turn all switches on?

#---- If "rcds=rcd1,rcd2,...,rcdN" then change the format for
#      "m/.../ parser to "^rcd1$|^rcd2$|^...$|^rcdN$"
if($rcds){$rcds =~ s/,/\$|^/g . '$';$rcds="\^$rcds\$";}
if($cds){$flds='';}                             # if cds, then turn all fields on
if($flds){$flds =~ s/,/\$|^/g . '$';$flds="\^$flds\$";}

#---- Define common print format and function (header, sub-heading):                          
$format="%-18s %7i = %-s\n";
$matches=0;
sub PRINT
{if($hdr)
   {if(! ($nfn || $nsn)){print "\n";}
    if(! $nfn)
      {if($station ne $ifn)
         {$hdr=qq/"$ifn" (record's stn=$station)/;}
       else{$hdr="$ifn";}
       printf $format,'FILENAME',$., "$hdr";
      }
    $hdr=0;
    ++$matches;
   }
 if("$TITLE")
   {if(!$nsn){printf $format,"$TITLE",$.,"$section (-----section header-----)";}
    $TITLE='';
   }
 printf $format,"$_[0]",$.,"\"$_[1]\"";
 ++$errors if $_[0] =~ m/^ERROR/;
}
#-------------------------------------------------------------------------------
#---- Open the file and read ISH records:
study $_;
open(IFN,$ifn) || Abort (qq/"$ifn" - $!/);
while (<IFN>)			
{#---- If user specified "rcds=rcd1,rcd2,...,rcdN ", then if record number
 #     then skip if currect record number is not one of the list:
 if($rcds){if($. !~ m/($rcds)/){next;}} 	# "$." = record number

 #---- Begin parsing record:
 chop;
 $i=length;                                     # length of "$_"
 if($i<105)
   {$TITLE=$section='';
    PRINT("\nERROR (rcd=$.)", 'incomplete or blank record');
    next;
   }
 #---- Extract station id from record:
 m/^....(.{6})(.{5})(.{4})/;$station="$1-$2-$3";
 
 #---- CDS and MDS (fixed format) section:
$hdr=1;					# turn on record header print
 if($cds || "$flds")
   {$TITLE='CDS';$section='CDS & MDS';
     for($i=0; $CDS_MDS[$i]<999; $i+=3)
       {$ele=$CDS_MDS[$i+2];
        if($flds){next if $ele !~ m/($flds)/;}
        $pos=$CDS_MDS[$i  ];
        $w=  $CDS_MDS[$i+1];
        PRINT($ele, substr($_,$pos,$w) ) if m/^.{$pos}(.{$w})+/;
        }
   }
 
 #---- ADDitional section:
 $_=substr($_,105);		             # remove CDS/MDS section
 if($add)
   {if(m/^ADD/)
      {$_=substr($_,3);                      # remove "ADD"
       $TITLE='ADD';$section='ADD';
       ADD: while(true)
         {m/^(IA[1-2]|[A-Z][A-Z])+/;
          $w=$add{$1};
          if(not m/^..[1-9]/)                # 3rd char must be 1-9
            {#---- Undefined, non-section header encountered.  Isolate and
             #     display the string and continue displaying good elements:
             last ADD if m/^(REM|EQD|QNN|AWY|MET|SYN|SOD|SOM)+/;
             $w=1;while(true)
               {++$w;
                m/^(.{$w})(IA.|..)(.)/;
                $undef="$1";
                $k="$2";
                if("$2$3" =~ m/^(REM|EQD|QNN|AWY|MET|SYN|SOD|SOM)+/)
                  {undef $k;last;}
                $k=$add{$k};
                last if $k;
               }
             PRINT (qq/ERROR (rcd=$.)/, qq/"$undef"/);
             $_=substr($_,$w);               # remove illegal field
             if($k){$w=$k;} else {last ADD;}
            }
          PRINT(m/(^...)/, m/(^.{$w})/);     # display current element
          $_=substr($_,$w);                  # remove  current element
          last if ! length;
         }
       }
   }
 #---- Remarks section:
 if($rem)
   {#---- Skip section if no remarks present:
    if(m/.*?(REM|AWY|MET|SYN|SOD|SOM)/)
      {#---- Strip record upto REM section:
       $w=index($_,$1);$_=substr($_,$w);        # strip down to beg of REMarks
       if($1 eq 'REM'){$_=substr($_,3);}	     # strip "REM"
       else {PRINT("ERROR (rcd=$.)", qq/"REM" section header missing/);}
       
       #---- Begin displaying remarks:
       $TITLE='REM';$section="REM's AWY/MET/SYN/SOD/SOM";
       while (m/.*?(AWY|MET|SYN|SOD|SOM)+/)
         {$w=index($_,$1);$_=substr($_,$w);
          $w=substr($_,3,3);                    # pluck the remark's length
          if($w<1){$_=substr($_,3);next;}
       
          #----- Verify AWY/MET/SYN/SOD/SOM's length:
          $k=substr($_,0,6);                    # remark subheader and length
          $ele=substr($_,$w+6,3);               # look past remark
          if($ele){$k='' if $ele =~ m/(AWY|MET|SYN|SOD|SOM|EQD|QNN)/;}
          else    {if(length($_)==($w+6)) {$k='';} else{$w=length($_)+6;} }
          PRINT("ERROR (rcd=$.)",qq/illegal remark length "$k"  following/) if $k;
       
          #---- display remark:
          $ele=substr($_,6,$w);
          PRINT(substr($_,0,6), qq/$ele/);
          $_=substr($_,6);
         }
      }
   }
 #---- EQD section:
 if($eqd)
   {$i=index($_,'EQD'); 				# strip off "EQD"
    if($i>-1)
      {$_ = substr($_,$i+3);
       $TITLE='EQD';$section='EQD';
       while (m/[N|P|Q|R]\d\d/)
	 {PRINT("EQD", substr($_,0,16));
	  $_=substr($_,16,16);
	 }
      }
   }
 #---- QNN section:
 if($qnn)
   {$i=index($_,'QNN');
    if($i>-1)
      {$_=substr($_,$i+3);				# strip off "QNN"
       $TITLE='QNN';$section='QNN';
       while(m/^[A-Y]/)
	 {PRINT('QNN',substr($_,0,11));
	  $_=substr($_,11,11);
	 }
      }
   }
}

#---- Done.  Issue closing messages:
$matches && Msg("$matches listed of $. records") || Msg ('no matches found');
$errors  && Emsg(" $errors found");
close IFN;
exit $errors;
__END__
=head1 NAME - isd_display.pl

=head1 SYNOPSIS - Extracts text fields from NCDC Integrated Surface Hourly data

=head1 DESCRIPTION
  perl routine reads a single file using command line options
to determine what field/sections to display.

=head1 required perl module:

 Set the directory pathname where "Cl_args.pm" resides to use this program.
For example,  if Cl_args.pm resides in directory, 
"/kerry/apps/ish/dev/scripts/util",  key in to the "use lib" line:
use lib qw(/kerry/apps/ish/dev/scripts/util);

=head1 COMMAND-LINE ARGUMENTS "[]"=optional:

  isd_display.pl [ifn=...] [all] [cds] [add] [rem] [eqd] [qnn]
    [flds=...] [rcds=...] [help] [def] [adh]

  ifn=input_file_name (required)
  rcds=...,...,  , ... (selected records)
    for example: rcds=1,18,100,..., default is all) 

  flds=...,...,  ,...  (show selected fixed position fields in CDS/MDS
  flds=(e.g., date,gmt_time,... use "def" help switch)           
  

  all (display all sections CDS/ADD/REM/EQD/QNN)                 

  The following switches are mutually exclusive with "all"       
  cds (display CDS & MDS section)                                
  add (display ADD section)                                      
  rem (display REM section)                                      
  eqd (display EQD section)                                      
  qnn (display QNN section)                                      

  The following permit suppression of header lines               
  nfn (suppress "FILENAME   =..." in record display)             
  nsn (supress section name display: e.g., "ADD (rcd=...)")        

  The following are mutually exclusive with all the above        
  help (verbose help)                                            
  def (displays CDS/MDS fixed position fields)                   
  adh (display ADD section field definitions)                    
  
=head2 INVOCATION EXAMPLES (argument order unimportant):

 isd_display.pl<enter> (show abreviated help)

 isd_display.pl ifn=some_file_name (show all records and all sections)

 isd_display.pl ifn=... add cds (show all records and cds and add sections)

 isd_display.pl ifn=... add rcds=1,18,22 (show add section of records 1,18,22)

 isd_display.pl ifn=... add flds=gmt,date,wind_speed,wind_direction,air_temp

 Informational:

 isd_display.pl def  (show CDS&MDS field descriptions)

 isd_display.pl help (show verbose help)

 isd_display.pl def adh (show CDS/MDS fields ADD field definitions)

AUTHOR
  Fred Smith (fred.smith@noaa.gov)
  TMC Inc. - Government Contractor
  National Climatic Data Center
  http://www.ncdc.noaa.gov
  11/2005
=cut

