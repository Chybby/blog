var gulp = require('gulp');
var sass = require('gulp-sass')(require('sass'));
var autoprefixer = require('gulp-autoprefixer');
var rename = require('gulp-rename');
var cssnano = require('gulp-cssnano');
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');
var notify = require('gulp-notify');
var del = require('del');
var rev = require('gulp-rev');
var revdel = require('gulp-rev-delete-original');

var paths = {
    styles: {
        src: 'css/blog.scss',
        dest: 'static/css/'
    },
    scripts: {
        src: 'js/*.js',
        dest: 'static/js/'
    }
};

function clean() {
    return del([paths.styles.dest, paths.scripts.dest]);
}

function styles() {
    return gulp.src(paths.styles.src)
        .pipe(sass())
        .pipe(autoprefixer('last 2 version'))
        .pipe(rename({ suffix: '.min' }))
        .pipe(cssnano())
        .pipe(gulp.dest(paths.styles.dest))
        .pipe(notify({ message: 'Styles task complete' }));
}

function scripts() {
    return gulp.src(paths.scripts.src)
        .pipe(concat('blog.js'))
        .pipe(rename({ suffix: '.min' }))
        .pipe(uglify())
        .pipe(gulp.dest(paths.scripts.dest))
        .pipe(notify({ message: 'Scripts task complete' }));
}

function rev_manifest() {
    return gulp.src(['static/css/*', 'static/js/*'], { base: 'static' })
        .pipe(rev())
        .pipe(revdel())
        .pipe(gulp.dest('static'))
        .pipe(rev.manifest({ merge: true }))
        .pipe(gulp.dest(process.cwd()));
}

var build = gulp.series(clean, gulp.parallel(styles, scripts), rev_manifest);

function watch() {
    gulp.watch('css/*.scss', build);
    gulp.watch(paths.scripts.src, build);
}


exports.clean = clean;
exports.styles = styles;
exports.scripts = scripts;
exports.rev_manifest = rev_manifest;
exports.watch = watch;
exports.build = build;

exports.default = build;