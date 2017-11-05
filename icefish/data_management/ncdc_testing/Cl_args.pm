#!/usr/local/bin/perl
#---- Package module to supply stdout, stderr, common messaging routines and
#     "cl_args" module for processing command line arguments.
#-------------------------------------------------------------------------------
package Cl_args;
require Exporter;
@ISA=qw(Exporter);
@EXPORT    = qw(Nsg Msg Emsg Quit Abort cl_args $TITLE $E $pn);
#@EXPORT_OK = qw(Nsg Msg Emsg Quit Abort cl_args $TITLE $E $pn);
use integer;                              # all integer operation
local $E;                                 # error indicator (false/true);
local $pn;                                # main program name;
local $TITLE;                             # user sets this

#---- Get program name prefix:
sub pn {my (@A); @A=split('/',$0); $pn=$A[$#A]; } # extract source name

#---- Define messaging functions:
sub Nsg   {defined($pn) || &pn;print $pn,':  ',@_;} # message w/o newline
sub Msg   {Nsg (@_,"\n");}		  # dislay  "@_" with newline to stdout
sub Emsg  {Msg @_;$E=1;}		  # error message with error flag set
sub Quit  {Msg (@_,'  Done.' );exit(0);}  # exit return
sub Abort {Msg (@_,'  Abort.');exit(1);}  # exit return with error indication

#---- Command line processing subroutine:
sub cl_args 
{use integer;
 ($I,$PAR,%HASH);

 #---- Command line arguments missing?  Issue instructions:
 if ($#ARGV<0)
  {$TITLE && Msg "$TITLE";                # print title if extant
   %HASH=
   ('r', '(required)',
    'o', '(optional)',
    's', '(switch  )',
    'h', '(help    )',
    'n' ,'    Note: '
   );
   Msg qq/Invocation (argument order unimportant):/;
   while ($I<$#_)
    {#---- build parameter description and defaults (if any):
     if($_[$I+2])
       {$PAR=qq/  $HASH{$_[$I+2]} $_[$I+1] "$_[$I+3]"/;}
     else 
       {$PAR=qq/  $HASH{$_[$I+2]} $_[$I+3]/;}	# "notes" line
      
     #---- Any default values?  append it if found:
     $_[$I] && {$PAR .=" DEFAULT=$_[$I]"};
     Msg $PAR;
     $I+=4;
    }
   exit(1);
 }
 
 #---- Reference optional "bucket" array?
 local($P,$A=$#_ & 3);			# "$A"'s value indicates presence of bucket
 $A || {local($B)=$_[$#_]};		# setup indirect reference to "bucket"

 #---- Process the command-line arguments left-to-right:
 my $required=1;			# flag to test for required args later
 ARGS:
 while (@ARGV)
  {$PAR=shift @ARGV;			# fetch a command-line parameter
   $P= $PAR=~/=/o ? "\L$`=" : "\L$PAR"; # load $P, delimit with "="
   if($HASH{$P}){Emsg qq/duplicate argument:  "$PAR"/;next ARGS;}
   #---- Scan for match against programmer's mnemonic definitions:
   $I=1;
   until ($I>$#_)
     {if($P eq "\L$_[$I]")		 # match? 
        {$_[$I-1]= $_[$I+1] =~ m/[s|h]/ ? $_[$I+1] : $' || shift @ARGV;
         if($_[$I-1] eq 'h'){$required=0;}
         $HASH{$P}=1;
         next ARGS;
        }
      $I+=4;				 # step to next mnemonic
     }
   #---- Scan exhausted, issue error or push into bucket:
   $A && {Emsg qq/illegal argument:  "$PAR"/}
      || {push(@$B,$PAR)};
  }

 #---- If a help switch was NOT specified, then check for missing required
 #     arguments:
 if($required)
   {#---- Check for missing "required" arguments:
    $I=2;
    until($I>$#_)
      {$_[$I] eq 'r'
        && {$_[$I-2] || {Emsg qq/required arg "$_[$I-1]..." missing/}};
       $I+=4;
      }
   }
 $E && exit 1;
}
1;

