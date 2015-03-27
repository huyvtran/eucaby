'use strict';

var SF_LAT = 37.7833;
var SF_LNG = -122.4167;

angular.module('eucaby.controllers', ['eucaby.services', 'eucaby.utils', 'eucaby.api'])

.controller('MainCtrl',
    ['$scope', '$rootScope', '$state', '$ionicSideMenuDelegate', 'EucabyApi',
    function($scope, $rootScope, $state, $ionicSideMenuDelegate, EucabyApi) {

    $rootScope.currentZoom = 13;

    $scope.showSideMenu = function(){
        return $scope.showHeader();
    };

    $scope.toggleRight = function(){
        $ionicSideMenuDelegate.toggleRight(!$ionicSideMenuDelegate.isOpenRight());
    };

    $scope.showHeader = function(){
        return $state.is('app.tab.map');  //!$state.is('app.login') || !
    };

    $scope.logout = function () {
        EucabyApi.logout();
        $state.go('app.login');
    };

//  $scope.rightButtons = [{
//    type: 'button-icon button-clear ion-navicon',
//    tap: function(e) {
//      $ionicSideMenuDelegate.toggleRight($scope.$$childHead);
//    }
//  }];
}])

.controller('LoginCtrl',
    ['$scope', '$location', '$ionicLoading', 'EucabyApi', 'utils',
     function($scope, $location, $ionicLoading, EucabyApi, utils) {

    $scope.facebookLogin = function(){

        $ionicLoading.show();
        EucabyApi.login().then(function () {
                $location.path('/app/tab/map');
            }, function(data) {
                utils.alert('Error', 'Error during log in. ' +
                                     'Please try again in a moment.');
                console.error(data);
            })
            .finally(function(){
                $ionicLoading.hide();
            });
    };
}])

.controller('MapCtrl', ['$scope', '$rootScope',
    '$http', '$ionicModal', '$ionicLoading', 'map', 'utils', 'Friends',
    function($scope, $rootScope,
             $http, $ionicModal, $ionicLoading, map, utils, Friends) {

    // Center on me action
    $scope.centerOnMe = function() {
        $ionicLoading.show();

        map.currentLocation(function(lat, lng){
            $scope.map = map.createMap('map', lat, lng,
                                       {zoom: $scope.currentZoom});
            google.maps.event.addListener(
                $scope.map, 'zoom_changed', function() {
                $rootScope.currentZoom = $scope.map.getZoom();
            });
            $scope.marker = map.createMarker($scope.map, lat, lng, 'Hello');
            $ionicLoading.hide();
        },
        function(data){
            $scope.map = map.createMap('map', SF_LAT, SF_LNG);
            $ionicLoading.hide();
            utils.alert('Location Error',
                        'Unable to get location: ' + data.message);
        });
    };

    $scope.centerOnMe();
    $scope.markers = [];

    var registerModal = function(template, modalName){
        $ionicModal.fromTemplateUrl(template, {
            scope: $scope
        }).then(function(modal) {
            $scope[modalName] = modal;
        });
    };

    registerModal('templates/request.html', 'requestModal');
    registerModal('templates/notify.html', 'notifyModal');

    $scope.$on('modal.shown', function(event, modal) {
        $ionicLoading.show();
        Friends.all().then(function(data){
            // XXX: Add cache for friends
            $scope.friends = data;
        }, function(data){
            utils.alert('Error', 'Error loading friends.');
            console.error(data);
        }).then(function(){
            if ($scope.notifyModal === modal){
                map.currentLocation(function(lat, lng){
                    $scope.notifyMap = map.createMap(
                        'notifymap', lat, lng, {zoom: 16});
                    $scope.currentMarker = map.createMarker(
                        $scope.notifyMap, lat, lng, 'Hello');
                    $rootScope.currentLatLng = {lat: lat, lng: lng};
                }, function(data){
                    utils.alert('Error',
                                'Failed to find the current location.');
                    console.error(data);
                });
            }
        }).finally(function(){
            $ionicLoading.hide();
        });


    });

    /*
    // Socket.io
    socket.on('connect', function(){
        console.log("Connected");
    });

    socket.on('message', function(message) {
        var msg = JSON.parse(message);
        clearOverlays($scope.markers);
        var marker = markerFactory(
            $scope.map, msg.location.lat, msg.location.lng,
            msg.session.receiver_email);
        $scope.markers.push(marker);
    });
    */
}])

.controller('NotificationCtrl',
    ['$scope', '$rootScope', 'Notification',
    function($scope, $rootScope, Notification) {

    $scope.form = {};
    $scope.sendLocation = function(){
        console.debug($rootScope.currentLatLng);
        Notification.post($scope.form, $rootScope.currentLatLng.lat,
                          $rootScope.currentLatLng.lng)
            .then(function(data){
            console.debug('Location submitted');
            $scope.notifyModal.hide();
        });
    };
}])

.controller('RequestCtrl',
    ['$scope', '$rootScope', 'Request', function($scope, $rootScope, Request) {

    $scope.form = {};

    // Send request action
    $scope.sendRequest = function(){
        Request.post($scope.form).then(function(data){
            console.debug('Request submitted');
            $scope.requestModal.hide();
        });
    };
}])

.controller('LogoutCtrl', function($scope) {

})

.controller('ProfileCtrl', function($scope) {
})

.controller('SettingsCtrl', function($scope) {
})

.controller('OutgoingCtrl',
    ['$scope', '$stateParams', '$ionicLoading', 'utils', 'Activity',
    function($scope, $stateParams, $ionicLoading, utils, Activity) {

    $ionicLoading.show();
    var formatOutgoing = function(data){
        var items = [];
        for (var i=0; i < data.length; i++){
            var item = data[i];
            var description = item.type.charAt(0).toUpperCase()
                + item.type.slice(1);
            description += ' sent on ' + item.created_date;  // XXX: Format date
            var url = '';
            if (item.type === 'notification'){
                url = '#/app/tab/outgoing_notification/' + item.id;
            } else if (item.type === 'request' && item.session.complete) {
                url = '#/app/tab/outgoing_request/' + item.id;
            }
            items.push({
                item: item,
                complete: item.session.complete,
                name: item.recipient.name || item.recipient.email,
                description: description,
                url: url
            });
        }
        return items;
    };

    var loadItems = function(){
        // Load outgoing items
        return Activity.outgoing().then(function(data){
            $scope.outgoing = formatOutgoing(data.data);
        }, function(data){
            utils.alert('Error', 'Error loading data');
            console.error(data);
        })
    };

    loadItems().finally(function(){
        $ionicLoading.hide();
    });

    $scope.refresh = function(){
        loadItems().finally(function(){
            $scope.$broadcast('scroll.refreshComplete');
        });
    }
}])

.controller('IncomingCtrl',
    ['$scope', '$stateParams', '$ionicLoading', 'utils', 'Activity',
    function($scope, $stateParams, $ionicLoading, utils, Activity) {

    $ionicLoading.show();
    var formatIncoming = function(data){
        var items = [];
        for (var i=0; i < data.length; i++){
            var item = data[i];
            var description = item.type.charAt(0).toUpperCase()
                + item.type.slice(1);
            description += ' received on ' + item.created_date;  // XXX: Format date
            var url = '';
            if (item.type === 'notification'){
                url = '#/app/tab/incoming_notification/' + item.id;
            } else if (item.type === 'request') {
                url = '#/app/tab/incoming_request/' + item.id;
            }
            items.push({
                item: item,
                complete: item.session.complete,
                name: item.sender.name,
                description: description,
                url: url
            });
        }
        return items;
    };

    var loadItems = function() {
        // Load incoming items
        return Activity.incoming().then(function (data) {
            $scope.incoming = formatIncoming(data.data);
        }, function (data) {
            utils.alert('Error', 'Error loading data');
            console.error(data);
        }).finally(function () {
            $ionicLoading.hide();
        });
    };

    loadItems().finally(function(){
        $ionicLoading.hide();
    });

    $scope.refresh = function(){
        loadItems().finally(function(){
            $scope.$broadcast('scroll.refreshComplete');
        });
    }
}])

.controller('NotificationDetailCtrl',
            ['$scope', '$ionicHistory', '$stateParams', 'map',
             'Notification',
    function($scope, $ionicHistory, $stateParams, map, Notification) {

        var stateName = $ionicHistory.currentView().stateName;
        $scope.isOutgoing = stateName.indexOf('outgoing') > -1;

        Notification.get($stateParams.id).then(function(data){
            var item = {
                data: data.data
            };
            $scope.item = item;
            var loc = $scope.item.data.location;
            $scope.map = map.createMap('locmap', loc.lat, loc.lng);
            $scope.marker = map.createMarker($scope.map, loc.lat, loc.lng, 'Hello');
        });
    }
])

.controller('RequestDetailCtrl',
            ['$scope', '$http', '$stateParams', 'map',
             'Request', 'Notification',
    function($scope, $http, $stateParams, map, Request, Notification) {

        var stateName = $scope.$viewHistory.currentView.stateName;
        $scope.isOutgoing = stateName.indexOf('outgoing') > -1;
        $scope.form = {};
        $scope.sendLocation = function(){
            Notification.post($scope.form, SF_LAT, SF_LNG).then(function(data){
                console.debug('Location submitted');
                // XXX: Reload the request view
            });
        };
        Request.get($stateParams.id).then(function(data){
            var item = {
                data: data.data
            };
            $scope.markers = [];
            $scope.map;
            $scope.item = item;
            $scope.form.token = item.data.session.token;
            for (var i = 0; i < item.data.notifications.length; i++){
                var notif = item.data.notifications[i];
                var loc = notif.location;
                if (!$scope.map) {
                    $scope.map = map.createMap('locmap', loc.lat, loc.lng);
                }
                $scope.markers.push(map.createMarker($scope.map, loc.lat, loc.lng, 'Hello'));
            }
        });
    }
]);
