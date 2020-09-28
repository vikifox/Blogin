"""
# coding:utf-8
@Time    : 2020/9/24
@Author  : jiangwei
@mail    : jiangwei1@kylinos.cn
@File    : auth
@Software: PyCharm
"""
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import or_

from blogin.forms.auth import RegisterForm, LoginForm
from blogin.models import User, LoginLog
from blogin.extension import db
from blogin.utils import get_ip_real_add, generate_token, Operations, validate_token
from blogin.emails import send_confirm_email

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')


@auth_bp.route('/register/', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.user_name.data
        pwd = form.confirm_pwd.data
        email = form.user_email.data.lower()
        user = User(username=name, email=email, password=pwd)
        user.set_password(pwd)
        user.set_role()
        db.session.add(user)
        db.session.commit()
        token = generate_token(user, operation='confirm')
        send_confirm_email(user=user, token=token)
        flash('注册成功,欢迎加入Blogin.', 'success')
        return redirect(url_for('.login'))
    return render_template('main/register.html', form=form)


@auth_bp.route('/login/', methods=['GET', 'POST'])
def login():
    # 若当前已有用户登录则返回主页
    if current_user.is_authenticated:
        return redirect(url_for('blog_bp.index'))
    form = LoginForm()
    if form.validate_on_submit():
        usr = form.usr_email.data
        pwd = form.password.data
        user = User.query.filter(or_(User.username==usr, User.email==usr.lower())).first()
        if user is not None and user.check_password(pwd):
            if login_user(user, form.remember_me.data):
                user.recent_login = datetime.now()
                remote_ip = request.remote_addr
                login_log = LoginLog(login_addr=remote_ip, user=user, real_addr=get_ip_real_add(remote_ip))
                db.session.add(login_log)
                db.session.commit()
                flash('登录成功!', 'success')
                return redirect(url_for('blog_bp.index'))
        elif user is None:
            flash('无效的邮箱或用户名.', 'danger')
        else:
            flash('无效的密码', 'danger')
    return render_template('main/login.html', form=form)


@auth_bp.route('/logout/', methods=['GET'])
@login_required
def logout():
    logout_user()
    flash('退出成功!', 'success')
    return redirect(url_for('blog_bp.index'))


@auth_bp.route('/confirm/<token>')
@login_required
def confirm(token):
    if validate_token(user=current_user, operation=Operations.CONFIRM, token=token):
        flash('邮箱确认成功!', 'success')
    else:
        flash('不是你的就别想有拥有啦!╭(╯^╰)╮  邮箱验证失败啦!', 'danger')
    return redirect(url_for('blog_bp.index'))