FROM kong:0.9.9

COPY init.sh /init.sh

CMD ["/init.sh"]

VOLUME /usr/local/kong
