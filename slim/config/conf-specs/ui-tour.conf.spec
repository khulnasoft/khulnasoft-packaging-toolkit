@placement search-head

#   Version 20170103
#
# This file contains the tours available for Khulnasoft Onboarding
#
# There is a default ui-tour.conf in $KHULNASOFT_HOME/etc/system/default.
# To create custom tours, place a ui-tour.conf in
# $KHULNASOFT_HOME/etc/system/local/. To create custom tours for an app, place
# ui-tour.conf in $KHULNASOFT_HOME/etc/apps/<app_name>/local/.
#
# To learn more about configuration files (including precedence) see the
# documentation located at
# http://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Admin/Aboutconfigurationfiles
#
# GLOBAL SETTINGS
# Use the [default] stanza to define any global settings.
#   * You can also define global settings outside of any stanza, at the top of
#     the file.
#   * This is not a typical conf file for configurations. It is used to set/create
#     tours to demonstrate product functionality to users.
#   * If an attribute is defined at both the global level and in a specific
#     stanza, the value in the specific stanza takes precedence.

[<stanza name>]
* Stanza name is the name of the tour

useTour = <string>
* Used to redirect this tour to another when called by Khulnasoft.
* Optional

nextTour = <string>
* String used to determine what tour to start when current tour is finished.
* Optional

intro = <string>
* A custom string used in a modal to describe what tour is about to be taken.
* Optional

type = <image || interactive>
* Can either be "image" or "interactive" to determine what kind of tour it is.
* Required

label = <string>
* The identifying name for this tour used in the tour creation app.
* Optional

tourPage = <string>
* The Khulnasoft view this tour is associated with (only necessary if it is linked to).
* Optional

viewed = <boolean>
* A boolean to determine if this tour has been viewed by a user.
* Set by Khulnasoft

############################
## For image based tours
############################
# Users can list as many images with captions as they want. Each new image is created by
# incrementing the number.

imageName<int> = <string>
* The name of the image file (example.png)
* Required but Optional only after first is set

imageCaption<int> = <string>
* The caption string for corresponding image
* Optional

imgPath = <string>
* The subdirectory relative to Khulnasoft's 'img' directory in which users put the images.
  This will be appended to the url for image access and not make a server request within Khulnasoft.
  EX) If user puts images in a subdirectory 'foo': imgPath = foo.
  EX) If within an app, imgPath = foo will point to the app's img path of
      appserver/static/img/foo
* Required only if images are not in the main 'img' directory.

context = <system || <specific app name>>
* String consisting of either 'system' or the app name the tour images are to be stored.
* If set to 'system', it will revert to Khulnasoft's native img path.
* Required


############################
## For interactive tours
############################
# Users can list as many steps with captions as they want. Each new step is created by
# incrementing the number.

urlData = <string>
* String of any querystring variables used with tourPage to create full url executing this tour.
* Optional

stepText<int> = <string>
* The string used in specified step to describe the UI being showcased.
* Required but Optional only after first is set

stepElement<int> = <selector>
* The UI Selector used for highlighting the DOM element for corresponding step.
* Optional

stepPosition<int> = <bottom || right || left || top>
* String that sets the position of the tooltip for corresponding step.
* Optional

stepClickEvent<int> = <click || mousedown || mouseup>
* Sets a specific click event for an element for corresponding step.
* Optional

stepClickElement<int> = <string>
* The UI selector used for a DOM element used in conjunction with click above.
* Optional
