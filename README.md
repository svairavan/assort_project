# assort_project
This is the code for the healthcare admin checkin


## Issues
1.)  Main issue is using chatgpt we are limited on how many requests we can do per minute so I had to put in a 10 second sleep time between requests.  So there are long pauses before the ai can respond and ask more questions.
2.) Sometimes the ai will cut off a response in the middle of talking.
3.) Pauses do not help much.  Need to figure out how to aggregate the response and then parse it
4.) The verification and parsing can be a bit better
5.) Though it is mostly consistent sometimes it interprets the wrong response and need to handle that
i.e if you say Allen it might hear ellen, helen, alan for a name.
6.) This is related to issue #3.  Sometimes when saying something we take a pause and the ai immediately thinks we are done talking and cuts off the response.  Again need to figure out how to aggregate.


## Like TODO if i had time

1.) Implement a scheduler so to use a programatically generated schedulr instead of hard coding
2.)  Right now the implementation is state based and tightly coupled.  I would like to decouple certain things and be more flexible and less state based on repsonses and questions.
3.) Instead of using chatgpt use chat4gpt locally but i couldn't use it as it was taking a lot of memory and slowing everything down.  Would be better to use it on an external server with better memory
4.) Would have like to implement a user verifcation so that if you say a phone number or name we can repeat it to verify what we heard was correct.  Maybe use the confidence parameter from deepgram to implement this feature.
5.)  Lot of things are hard coded. Decoupling would make it easier to read, maintain, and update.
