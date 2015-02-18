'use strict';

var EUCABY_ENDPOINT = 'http://api.eucaby-dev.appspot.com';
var TEMP_TOKEN = 'Dvhn5yO4E6EMtJnJ0PQDI0fpROMqN2';

angular.module('eucaby.services', ['ngResource', 'eucaby.api'])

.factory('Friends', ['EucabyApi', function(EucabyApi) {

    return EucabyApi.api({path: '/friends'});
}])

.factory('Activity', ['$resource', function($resource) {

    return $resource(EUCABY_ENDPOINT + '/history', {}, {
        outgoing: {method: 'GET', params: {type: 'outgoing'},
            headers: {'Authorization': 'Bearer ' + TEMP_TOKEN}
        },
        incoming: {method: 'GET', params: {type: 'incoming'},
            headers: {'Authorization': 'Bearer ' + TEMP_TOKEN}
        }
    });
}])
.factory('NotificationDetail', ['$resource', function($resource) {

    return $resource(EUCABY_ENDPOINT + '/location/notification/:id', {}, {
        get: {method: 'GET',
            headers: {'Authorization': 'Bearer ' + TEMP_TOKEN}
        }
    });
}])
.factory('RequestDetail', ['$resource', function($resource) {

    return $resource(EUCABY_ENDPOINT + '/location/request/:id', {}, {
        get: {method: 'GET',
            headers: {'Authorization': 'Bearer ' + TEMP_TOKEN}
        }
    });
}]);
