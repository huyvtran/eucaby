'use strict';

angular.module('eucaby',
    ['ionic', 'openfb', 'btford.socket-io', 'eucaby.controllers',
     'eucaby.services'])

.factory('socket', function (socketFactory) {
    return socketFactory({
        ioSocket: io('http://localhost:4000') // rt.eucaby-dev.appspot.com, 146.148.67.189
    });
})

.run(function($rootScope, $state, $ionicPlatform, $window, OpenFB) {

    OpenFB.init('809426419123624'); //, 'http://localhost:8100/oauthcallback.html');

    $ionicPlatform.ready(function() {
        if(window.StatusBar) {
            // org.apache.cordova.statusbar required
            StatusBar.styleDefault();
        }
    });

    $rootScope.$on('$stateChangeStart', function(event, toState) {
        if (toState.name !== 'app.login' && toState.name !== 'app.logout' && !$window.sessionStorage['fbtoken']) {
            $state.go('app.login');
            event.preventDefault();
        }
    });

    $rootScope.$on('OAuthException', function() {
        $state.go('app.login');
    });

})

.config(function($stateProvider, $urlRouterProvider) {

    $stateProvider

    // Abstract states
    .state('app', {
        url: '/app',
        abstract: true,
        templateUrl: 'templates/menu.html'
    })

    .state('app.tabs', {
        url: '/tab',
        abstract: true,
        views: {
            'menu-content': {
                templateUrl: 'templates/tabs.html'
            }
        }
    })

    // States with navigation history stack
    .state('app.login', {
        url: '/login',
        views: {
            'menu-content': {
                templateUrl: 'templates/login.html',
                controller: 'LoginCtrl'
            }
        }
    })

    .state('app.logout', {
        url: '/logout',
        views: {
            'menu-content': {
                templateUrl: 'templates/logout.html',
                controller: 'LogoutCtrl'
            }
        }
    })

    .state('app.tabs.map', {
        url: '/map',
        views: {
            'tab-map': {
                templateUrl: 'templates/tab-map.html',
                controller: 'MapCtrl'
            }
        }
    })
    .state('app.tabs.map.request', { // Not working
        url: '/request',
        views: {
            'tab-map': {
                template: 'templates/tab-down.html',
                controller: 'RequestCtrl'
            }
        }
    })
    .state('app.tabs.friends', {
        url: '/friends',
        views: {
            'tab-friends': {
                templateUrl: 'templates/tab-friends.html',
                controller: 'FriendsCtrl'
            }
        }
    })
    .state('app.tabs.friend-detail', {
        url: '/friend/:friendId',
        views: {
            'tab-friends': {
                templateUrl: 'templates/friend-detail.html',
                controller: 'FriendDetailCtrl'
            }
        }
    })

    .state('app.tabs.down', {
        url: '/down',
        views: {
            'tab-down': {
                templateUrl: 'templates/tab-down.html',
                controller: 'DownCtrl'
            }
        }
    });

  $urlRouterProvider.otherwise('/app/tab/map');

});


